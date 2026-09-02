/* Fecha:    2026-09-02
   Analista: Juanes
   Objetivo: proyectar la pérdida terminal **ponderada por dólares**, que es la cifra que entra
             en el modelo de suscripción. La de conteo cuenta el mecanismo; esta cuesta dinero.
   Entrada:  curvas, cohortes, prestamos. Variable: horizonte (meses), fijada por analizar.py.
   Salida:   factores_desarrollo_usd — factor mediano y banda por edad, en dólares
             proyeccion_terminal_usd — una fila por cohorte

   POR QUÉ ESTO NO ES 04_proyeccion.sql CON OTRA COLUMNA. La tentación es multiplicar la tasa en
   dólares por los factores de desarrollo del conteo. Sería un número inventado: las dos curvas
   maduran a velocidades distintas y el cociente entre ambas NO es constante, cae con la edad.

     FY2012 a 138 meses:  6,08 % conteo · 2,77 % dólares -> ratio 0,456
     FY2018 a  93 meses:  7,55 % conteo · 2,59 % dólares -> ratio 0,343
     FY2023 a  33 meses:  2,39 % conteo · 0,54 % dólares -> ratio 0,226

   Tiene sentido: los préstamos que fallan pronto llevan poco amortizado, y los grandes —que pesan
   en dólares y poco en conteo— fallan menos y más tarde. Así que los factores en dólares se
   calculan sobre la curva en dólares, con las mismas 24 añadas completas y el mismo umbral.

   QUÉ MIDE ESTA TASA, EXACTAMENTE. `tasa_acum_usd_pct` es *importe fallido ÷ importe aprobado en
   origen*: céntimos perdidos por cada dólar aprobado. NO es pérdida sobre saldo vivo, NO es
   severidad (LGD) y NO es pérdida neta — el archivo no registra recuperaciones. El numerador es
   el saldo pendiente en el momento del fallido y el denominador el importe original, así que la
   amortización ya está dentro. Quien lo compare con una LGD se equivocará, y por eso la etiqueta
   viaja con el número hasta la ficha de recomendación.
*/

CREATE OR REPLACE TABLE factores_desarrollo_usd AS

WITH completas AS (
  SELECT cohorte FROM cohortes
  WHERE edad_min_observable >= getvariable('horizonte')
),

pares AS (
  SELECT c.cohorte, c.edad,
         c.tasa_acum_usd_pct AS tasa_en_edad,
         h.tasa_acum_usd_pct AS tasa_en_horizonte
  FROM curvas c
  JOIN completas USING (cohorte)
  JOIN curvas h
    ON  h.cohorte   = c.cohorte
    AND h.dimension = 'global'
    AND h.nivel     = 'todos'
    AND h.edad      = getvariable('horizonte')
  WHERE c.dimension = 'global'
    AND c.nivel     = 'todos'
    AND c.edad     <= getvariable('horizonte')
    AND c.tasa_acum_usd_pct > 0      -- sin esto, f = infinito y la mediana se corrompe
)

SELECT
  edad,
  count(*)                                                          AS cohortes_completas,
  round(median(tasa_en_horizonte / tasa_en_edad), 4)                AS factor_mediano,
  round(quantile_cont(tasa_en_horizonte / tasa_en_edad, 0.25), 4)   AS factor_q1,
  round(quantile_cont(tasa_en_horizonte / tasa_en_edad, 0.75), 4)   AS factor_q3
FROM pares
GROUP BY edad;


CREATE OR REPLACE TABLE proyeccion_terminal_usd AS

/* La tasa cruda en dólares no está en `cohortes`, así que se calcula aquí desde la población.
   Numerador: TODO el importe fallido, incluidos los 90 fallidos sin fecha utilizable — fallaron
   y costaron dinero aunque no se puedan colocar en la curva. */
WITH cruda AS (
  SELECT cohorte,
         round(100.0 * sum(importe_fallido) / sum(importe_aprobado), 4) AS tasa_cruda_usd_pct,
  -- Redondeado a centavos: sumar millones de dobles en paralelo no es asociativo, y sin
  -- esto el CSV salia distinto en cada ejecucion (…259.01 contra …259.0099998) sin que
  -- cambiara nada analitico. Un diff que aparece solo es un diff que nadie mira.
         round(sum(importe_aprobado), 2) AS usd_en_riesgo
  FROM prestamos
  WHERE NOT cohorte_parcial
  GROUP BY cohorte
),

lectura AS (
  SELECT c.cohorte,
         c.en_riesgo,
         c.edad_min_observable,
         least(3 * CAST(floor(c.edad_min_observable / 3.0) AS INTEGER),
               getvariable('horizonte'))                   AS edad_lectura,
         c.edad_min_observable >= getvariable('horizonte')  AS completa
  FROM cohortes c
),

observado AS (
  SELECT l.*, cr.tasa_cruda_usd_pct, cr.usd_en_riesgo,
         cu.tasa_acum_usd_pct AS tasa_observada_usd
  FROM lectura l
  JOIN cruda cr USING (cohorte)
  JOIN curvas cu
    ON  cu.cohorte   = l.cohorte
    AND cu.dimension = 'global'
    AND cu.nivel     = 'todos'
    AND cu.edad      = l.edad_lectura
)

SELECT
  o.cohorte,
  o.en_riesgo,
  o.usd_en_riesgo,
  o.completa,
  o.edad_lectura,
  o.tasa_cruda_usd_pct,
  o.tasa_observada_usd,
  f.factor_mediano,
  round(100.0 / f.factor_mediano, 2)                       AS pct_perdida_ya_realizada,

  -- Mismo umbral que en conteo: hace falta haber visto al menos el 10 % de la pérdida eventual.
  (o.completa OR f.factor_mediano <= 10)                   AS proyectable,

  CASE WHEN o.completa             THEN o.tasa_observada_usd
       WHEN f.factor_mediano <= 10 THEN round(o.tasa_observada_usd * f.factor_mediano, 4)
       ELSE NULL END                                       AS terminal_usd_pct,
  CASE WHEN o.completa             THEN o.tasa_observada_usd
       WHEN f.factor_mediano <= 10 THEN round(o.tasa_observada_usd * f.factor_q1, 4)
       ELSE NULL END                                       AS terminal_usd_q1_pct,
  CASE WHEN o.completa             THEN o.tasa_observada_usd
       WHEN f.factor_mediano <= 10 THEN round(o.tasa_observada_usd * f.factor_q3, 4)
       ELSE NULL END                                       AS terminal_usd_q3_pct
FROM observado o
LEFT JOIN factores_desarrollo_usd f ON f.edad = o.edad_lectura
ORDER BY o.cohorte;
