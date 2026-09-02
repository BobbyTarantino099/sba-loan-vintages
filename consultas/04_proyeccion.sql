/* Fecha:    2026-09-01
   Analista: Juanes
   Objetivo: proyectar la pérdida terminal de las cohortes inmaduras a partir de la forma de
             maduración de las completas, por el método de factores de desarrollo.
   Entrada:  curvas, cohortes. Variable: horizonte (meses), fijada por analizar.py.
   Salida:   factores_desarrollo — un factor mediano y su banda por cada edad
             proyeccion_terminal — una fila por cohorte, con lo observado y lo proyectado

   El método es el que usa un equipo de riesgo, y no tiene nada de aprendizaje automático: si las
   cohortes completas han realizado, digamos, la mitad de su pérdida a los 60 meses, entonces una
   cohorte que hoy tiene 60 meses y lleva un 3 % probablemente termine cerca del 6 %.

   Se usa la MEDIANA de los factores entre cohortes, no la media: FY2007 perdió el doble que sus
   vecinas y arrastraría la media él solo.

   Se publica una BANDA (Q1-Q3 de los factores), no un punto. Un punto sería una precisión que el
   método no tiene, y la anchura de la banda es justamente el mensaje para las cohortes jóvenes:
   a los 9 meses de vida no hay forma de saber cómo va a terminar una añada, y el gráfico tiene
   que decirlo en vez de disimularlo.

   Salvaguarda: los factores solo se calculan donde la tasa observada es > 0. Dividir por cero da
   infinito, e infinito propagado a una mediana la destruye en silencio.
*/

CREATE OR REPLACE TABLE factores_desarrollo AS

WITH completas AS (
  SELECT cohorte FROM cohortes
  WHERE edad_min_observable >= getvariable('horizonte')
),

/* Para cada cohorte completa: lo que llevaba a cada edad, y lo que acabó teniendo en H. */
pares AS (
  SELECT c.cohorte, c.edad, c.tasa_acum_pct AS tasa_en_edad, h.tasa_acum_pct AS tasa_en_horizonte
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
    AND c.tasa_acum_pct > 0        -- sin esto, f = infinito y la mediana se corrompe
)

SELECT
  edad,
  count(*)                                                AS cohortes_completas,
  round(median(tasa_en_horizonte / tasa_en_edad), 4)      AS factor_mediano,
  round(quantile_cont(tasa_en_horizonte / tasa_en_edad, 0.25), 4) AS factor_q1,
  round(quantile_cont(tasa_en_horizonte / tasa_en_edad, 0.75), 4) AS factor_q3
FROM pares
GROUP BY edad;


CREATE OR REPLACE TABLE proyeccion_terminal AS

/* La edad a la que se lee cada cohorte: la mayor de la rejilla que todos sus préstamos han
   alcanzado. Una cohorte completa se lee directamente en H y no necesita proyección. */
WITH lectura AS (
  SELECT c.cohorte,
         c.en_riesgo,
         c.edad_min_observable,
         c.tasa_cruda_pct,
         least(3 * CAST(floor(c.edad_min_observable / 3.0) AS INTEGER),
               getvariable('horizonte'))                  AS edad_lectura,
         c.edad_min_observable >= getvariable('horizonte') AS completa
  FROM cohortes c
),

observado AS (
  SELECT l.*, cu.tasa_acum_pct AS tasa_observada
  FROM lectura l
  JOIN curvas cu
    ON  cu.cohorte   = l.cohorte
    AND cu.dimension = 'global'
    AND cu.nivel     = 'todos'
    AND cu.edad      = l.edad_lectura
)

SELECT
  o.cohorte,
  o.en_riesgo,
  o.completa,
  o.edad_min_observable,
  o.edad_lectura,
  o.tasa_cruda_pct,                                        -- lo que diría un GROUP BY sin pensar
  o.tasa_observada,                                        -- lo mismo, pero leído a edad_lectura
  f.factor_mediano,
  round(100.0 / f.factor_mediano, 2)                       AS pct_perdida_ya_realizada,

  /* Umbral de proyectabilidad: hace falta haber visto al menos el 10 % de la pérdida eventual,
     o sea un factor <= 10. Por encima de eso el multiplicador amplifica ruido y devuelve un
     número de aspecto preciso construido sobre casi nada — FY2025 tiene un factor de 606, y
     multiplicar su 0,005 % observado da un 3 % que no significa absolutamente nada.

     El umbral se fijó DESPUÉS de ver los factores, y así queda dicho. No se eligió para que
     saliera una conclusión: se eligió porque publicar la proyección de FY2025 sería cometer, en
     la última figura del caso, el mismo error que el caso denuncia en la primera. Para esas
     cohortes se publica el hueco, que es la respuesta honesta. */
  (o.completa OR f.factor_mediano <= 10)                   AS proyectable,

  CASE WHEN o.completa                  THEN o.tasa_observada
       WHEN f.factor_mediano <= 10      THEN round(o.tasa_observada * f.factor_mediano, 4)
       ELSE NULL END                                       AS terminal_proyectado_pct,
  CASE WHEN o.completa                  THEN o.tasa_observada
       WHEN f.factor_mediano <= 10      THEN round(o.tasa_observada * f.factor_q1, 4)
       ELSE NULL END                                       AS terminal_q1_pct,
  CASE WHEN o.completa                  THEN o.tasa_observada
       WHEN f.factor_mediano <= 10      THEN round(o.tasa_observada * f.factor_q3, 4)
       ELSE NULL END                                       AS terminal_q3_pct
FROM observado o
LEFT JOIN factores_desarrollo f ON f.edad = o.edad_lectura
ORDER BY o.cohorte;
