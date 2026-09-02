/* Fecha:    2026-09-01
   Analista: Juanes
   Objetivo: llevar el crudo a la población de análisis de la fase 1 — los préstamos que de
             verdad pusieron dinero en riesgo — y etiquetar cada fila con la cohorte, la edad y
             los tramos que el análisis va a cortar.
   Entrada:  raw_7a
   Salida:   prestamos — una fila = un préstamo desembolsado. 1.697.539 filas esperadas.

   Decisiones que esta consulta materializa, todas razonadas en bitacora-limpieza.md:

     · población = 'P I F' + 'CHGOFF' + 'EXEMPT'   -> los desembolsados
     · fuera 'CANCLD' (242.790) y 'COMMIT' (21.123) -> nunca se desembolsaron: no pueden estar
       ni en el numerador ni en el denominador de una tasa de pérdida
     · fuera importe <= 0 (3 filas)                 -> ruido, contado en la bitácora
     · plazo 0 o > 360 meses -> tramo 'unknown'     -> se conservan en la curva global
     · NAICS nulo -> sector 'unknown'               -> el corte por sector se limita a FY2001+
     · FY2026 marcado como cohorte parcial          -> fuera de toda comparación entre añadas
     · duplicados NO eliminados                     -> son préstamos distintos, ver bitácora

   EL PUNTO QUE DECIDE EL CASO. 'EXEMPT' no significa "desconocido": el diccionario oficial lo
   define como préstamo desembolsado que no ha sido cancelado, ni pagado, ni fallido. Es decir,
   VIVO a la fecha de corte. Entra en el denominador como población en riesgo que todavía no ha
   sufrido el evento — que es exactamente lo que la censura por la derecha significa. Excluirlo
   borraría casi toda la población reciente y haría que las añadas nuevas parecieran impecables.

   date_diff('month', a, b) en DuckDB cuenta fronteras de mes cruzadas, no meses completos de 30
   días. Es la convención que se quiere para una curva de maduración: un préstamo aprobado el 30
   de junio y fallido el 1 de julio tiene edad 1, no 0.
*/

CREATE OR REPLACE TABLE prestamos AS

WITH desembolsados AS (
  SELECT *
  FROM raw_7a
  WHERE estado IN ('P I F', 'CHGOFF', 'EXEMPT')   -- literal, sensible a mayúsculas y con espacios
    AND importe_aprobado > 0
),

etiquetados AS (
  SELECT
    archivo_origen,
    fecha_corte,
    fecha_aprobacion,
    fecha_fallido,
    importe_aprobado,
    importe_garantizado,
    importe_fallido,
    plazo_meses,
    estado,
    revolvente,
    metodo_proceso,
    naics,
    naics_descripcion,
    estado_proyecto,
    lender_id,
    banco_actual,

    -- La cohorte es el año fiscal de aprobación. FY federal: del 1 de octubre al 30 de septiembre.
    anio_fiscal                                                      AS cohorte,

    /* FY2026 va del 2025-10-01 al 2026-09-30, pero el corte de los datos es el 2026-06-30: solo
       tiene nueve meses de aprobaciones. Se conserva para los conteos y se excluye de cualquier
       comparación entre añadas, donde compararía nueve meses contra doce. */
    (anio_fiscal = 2026)                                             AS cohorte_parcial,

    estado = 'CHGOFF'                                                AS fallido,

    /* Fallidos cuya fecha no se puede usar. Son dos poblaciones distintas con el mismo destino:

         · 58 marcados CHGOFF sin ninguna fecha de fallido.
         · 32 con fecha POSTERIOR a la fecha de corte del propio publicador — 31 el 2026-07-01,
           un día después del corte, y uno el 2026-10-22, casi cuatro meses después. El archivo
           se contradice a sí mismo: su AsOfDate dice 2026-06-30. No se sabe si el corte real es
           otro o si son errores de captura, y no hace falta saberlo para decidir qué hacer.

       Ambas cuentan en la tasa terminal — fallaron — pero no se pueden colocar en la curva,
       porque no se sabe cuándo. Se marcan aquí para excluirlas del numerador por edad sin
       sacarlas de la población. Son 90 de 220.688 fallidos: 0,04%.

       Lo que NO se hace: recortar la fecha al corte. Inventaría una edad al fallido que nadie
       observó, y encima la pondría toda en el mismo mes, creando un pico artificial justo en el
       extremo derecho de la curva, que es donde el caso hace su afirmación. */
    (estado = 'CHGOFF'
       AND (fecha_fallido IS NULL OR fecha_fallido > fecha_corte))   AS fallido_sin_fecha_util,

    CASE
      WHEN fecha_fallido IS NOT NULL AND fecha_fallido <= fecha_corte
        THEN date_diff('month', fecha_aprobacion, fecha_fallido)
      ELSE NULL
    END                                                              AS edad_al_fallido,

    date_diff('month', fecha_aprobacion, fecha_corte)                AS edad_observable,

    CASE
      WHEN plazo_meses IS NULL      THEN 'unknown'
      WHEN plazo_meses <= 0         THEN 'unknown'   -- 1.359 filas, la mitad revolventes
      WHEN plazo_meses > 360        THEN 'unknown'   -- 85 filas, hasta 569 meses, ninguna revolvente
      WHEN plazo_meses <= 84        THEN '01 <= 7a'
      WHEN plazo_meses <= 120       THEN '02 7-10a'
      WHEN plazo_meses <= 240       THEN '03 10-20a'
      ELSE                               '04 > 20a'
    END                                                              AS tramo_plazo,

    /* Sector NAICS de dos dígitos. Tres sectores se publican como rango y hay que colapsarlos,
       o Manufactura aparecería partida en tres barras que nadie sabría sumar. */
    CASE
      WHEN naics IS NULL                          THEN 'unknown'
      WHEN substr(naics, 1, 2) IN ('31','32','33') THEN '31-33'
      WHEN substr(naics, 1, 2) IN ('44','45')      THEN '44-45'
      WHEN substr(naics, 1, 2) IN ('48','49')      THEN '48-49'
      ELSE substr(naics, 1, 2)
    END                                                              AS sector,

    /* Cuartil de importe DENTRO de su cohorte, no sobre toda la historia. Un préstamo de
       100.000 $ era grande en 1993 y es mediano en 2025: cuartilar globalmente convertiría el
       tramo de importe en un reloj disfrazado y el corte mediría inflación, no riesgo. */
    ntile(4) OVER (PARTITION BY anio_fiscal ORDER BY importe_aprobado) AS cuartil_importe

  FROM desembolsados
)

SELECT
  *,
  CASE cuartil_importe
    WHEN 1 THEN '01 Q1 menor'
    WHEN 2 THEN '02 Q2'
    WHEN 3 THEN '03 Q3'
    WHEN 4 THEN '04 Q4 mayor'
    ELSE        'unknown'
  END AS tramo_importe
FROM etiquetados;
