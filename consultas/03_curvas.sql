/* Fecha:    2026-09-01
   Analista: Juanes
   Objetivo: construir la matriz añada × edad — la tasa acumulada de fallidos de cada cohorte a
             cada edad — para el conjunto y para los tres cortes (plazo, importe, sector).
   Entrada:  prestamos
   Salida:   cohortes  (una fila = una cohorte, con su población y su edad máxima legible)
             curvas    (una fila = cohorte × dimensión × nivel × edad)

   El denominador se fija en el origen y NO se mueve: es la población en riesgo de la cohorte,
   incluidos los préstamos vivos ('EXEMPT'). Es lo que distingue una curva de maduración de un
   simple recuento acumulado — el préstamo vivo no ha fallado *todavía*, y esa es información.

   Rejilla de edades cada 3 meses, de 0 a 240. Los tres cortes del análisis (36, 60, 84), los
   candidatos a horizonte terminal y la edad de referencia con la que se deriva (240) caen todos
   en múltiplos de 3, así que ninguno se interpola. La exportación al sitio se recorta luego a
   120 meses: la rejilla larga existe para poder derivar el horizonte, no para publicarla.

   Los eventos se agrupan al múltiplo de 3 SUPERIOR (`3 * ceil(edad/3)`), de forma que el
   acumulado en la edad g sea exactamente el número de fallidos con edad <= g. Redondear al
   inferior adelantaría fallidos y curvaría la maduración hacia arriba.

   `observable` marca hasta dónde se puede leer cada cohorte: solo hasta la edad que TODOS sus
   préstamos han alcanzado, que la fija su última aprobación. Más allá, la fila existe pero la
   tasa está subestimada porque parte de la cohorte aún no ha llegado ahí. Ninguna comparación
   entre cohortes puede usar filas con observable = false.
*/

CREATE OR REPLACE TABLE cohortes AS
SELECT
  cohorte,
  count(*)                                          AS en_riesgo,
  sum(importe_aprobado)                             AS usd_en_riesgo,
  min(edad_observable)                              AS edad_min_observable,
  count(*) FILTER (WHERE fallido)                   AS fallidos_totales,
  count(*) FILTER (WHERE fallido_sin_fecha_util)    AS fallidos_sin_fecha,
  count(*) FILTER (WHERE estado = 'EXEMPT')         AS vivos,
  round(100.0 * count(*) FILTER (WHERE fallido) / count(*), 4) AS tasa_cruda_pct
FROM prestamos
WHERE NOT cohorte_parcial          -- FY2026 tiene 9 meses de aprobaciones, no 12
GROUP BY cohorte;


CREATE OR REPLACE TABLE curvas AS

/* Cada préstamo aparece una vez por dimensión. Cuesta 4 x 1,7 M filas intermedias y ahorra
   escribir el mismo cálculo cuatro veces, que es la vía rápida a que uno de los cuatro se
   quede sin actualizar cuando cambie la definición. */
WITH largo AS (
  SELECT cohorte, edad_al_fallido, fallido, fallido_sin_fecha_util,
         importe_aprobado, importe_fallido,
         'global' AS dimension, 'todos' AS nivel
  FROM prestamos WHERE NOT cohorte_parcial

  UNION ALL
  SELECT cohorte, edad_al_fallido, fallido, fallido_sin_fecha_util,
         importe_aprobado, importe_fallido,
         'plazo', tramo_plazo
  FROM prestamos WHERE NOT cohorte_parcial

  UNION ALL
  SELECT cohorte, edad_al_fallido, fallido, fallido_sin_fecha_util,
         importe_aprobado, importe_fallido,
         'importe', tramo_importe
  FROM prestamos WHERE NOT cohorte_parcial

  UNION ALL
  SELECT cohorte, edad_al_fallido, fallido, fallido_sin_fecha_util,
         importe_aprobado, importe_fallido,
         'sector', sector
  FROM prestamos WHERE NOT cohorte_parcial AND cohorte >= 2001   -- NAICS no existe antes
),

/* Denominadores por celda, fijados en el origen. */
poblacion AS (
  SELECT cohorte, dimension, nivel,
         count(*)               AS en_riesgo,
         sum(importe_aprobado)  AS usd_en_riesgo
  FROM largo GROUP BY 1, 2, 3
),

eventos AS (
  SELECT cohorte, dimension, nivel,
         3 * CAST(ceil(edad_al_fallido / 3.0) AS INTEGER) AS edad,
         count(*)                                         AS n_fallidos,
         sum(importe_fallido)                             AS usd_fallido
  FROM largo
  WHERE fallido AND NOT fallido_sin_fecha_util
  GROUP BY 1, 2, 3, 4
),

rejilla AS (
  SELECT p.cohorte, p.dimension, p.nivel, p.en_riesgo, p.usd_en_riesgo,
         c.edad_min_observable, g.edad
  FROM poblacion p
  JOIN cohortes c USING (cohorte)
  CROSS JOIN (SELECT unnest(generate_series(0, 240, 3)) AS edad) g
)

SELECT
  r.cohorte,
  r.dimension,
  r.nivel,
  r.edad,
  r.en_riesgo,
  sum(coalesce(e.n_fallidos, 0)) OVER v                                   AS fallidos_acum,
  round(100.0 * sum(coalesce(e.n_fallidos, 0)) OVER v / r.en_riesgo, 4)   AS tasa_acum_pct,
  sum(coalesce(e.usd_fallido, 0)) OVER v                                  AS usd_acum,
  round(100.0 * sum(coalesce(e.usd_fallido, 0)) OVER v / r.usd_en_riesgo, 4) AS tasa_acum_usd_pct,
  r.edad <= r.edad_min_observable                                         AS observable
FROM rejilla r
LEFT JOIN eventos e
  ON  e.cohorte   = r.cohorte
  AND e.dimension = r.dimension
  AND e.nivel     = r.nivel
  AND e.edad      = r.edad
WINDOW v AS (PARTITION BY r.cohorte, r.dimension, r.nivel ORDER BY r.edad);
