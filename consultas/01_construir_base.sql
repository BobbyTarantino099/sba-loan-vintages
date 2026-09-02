/* Fecha:    2026-09-01
   Analista: Juanes
   Objetivo: cargar los cuatro extractos FOIA del programa 7(a) en una sola tabla tipada.
             NO filtra, NO corrige y NO deriva nada: eso es 02_poblacion.sql. Aquí solo se
             pasa de texto a tipos, para que cualquier pérdida de filas posterior sea
             atribuible a una decisión y no a la carga.
   Entrada:  los cuatro CSV de datos/crudos/, vía la variable ruta_crudos
   Salida:   raw_7a — una fila = una aprobación de préstamo. 1.961.455 filas esperadas.

   Notas de la fuente, todas comprobadas el 2026-08-31 y anotadas en la ficha de fuente:

     · Los cuatro archivos comparten cabecera idéntica de 42 columnas, así que se leen con un
       glob y no hay conciliación de esquemas que hacer. Se conserva `archivo_origen` para poder
       atribuir cualquier anomalía a su década.

     · Se lee con all_varchar y se castea aquí de forma explícita, en vez de dejar que DuckDB
       infiera tipos. Con cuatro archivos, la inferencia puede resolver distinto en cada uno y
       la diferencia no se nota hasta que una suma sale mal.

     · DuckDB compara cadenas de forma SENSIBLE a mayúsculas. `estado` se conserva literal, con
       sus espacios: el valor de "pagado en su totalidad" es 'P I F', no 'PIF'. Verificado el
       2026-08-31.

     · `RevolverStatus` llega como 'Y'/'N' aunque el diccionario oficial lo documente como
       0 = plazo / 1 = revolvente. Se respeta lo que trae el archivo y se deja constancia:
       el diccionario del publicador no siempre describe su propio volcado.
*/

CREATE OR REPLACE TABLE raw_7a AS
SELECT
  regexp_extract(filename, 'sba_7a_([0-9-]+)_', 1)   AS archivo_origen,

  -- Identidad y fechas
  CAST(AsOfDate      AS DATE)                        AS fecha_corte,
  CAST(ApprovalDate  AS DATE)                        AS fecha_aprobacion,
  CAST(ApprovalFY    AS INTEGER)                     AS anio_fiscal,
  TRY_CAST(FirstDisbursementDate AS DATE)            AS fecha_primer_desembolso,
  TRY_CAST(PaidInFullDate        AS DATE)            AS fecha_pago_total,
  TRY_CAST(ChargeOffDate         AS DATE)            AS fecha_fallido,

  -- Importes. TRY_CAST y no CAST: si alguna vez llega un importe no numérico, se quiere un
  -- NULL contable y no una excepción que tumbe la carga entera.
  TRY_CAST(GrossApproval         AS DOUBLE)          AS importe_aprobado,
  TRY_CAST(SBAGuaranteedApproval AS DOUBLE)          AS importe_garantizado,
  TRY_CAST(GrossChargeOffAmount  AS DOUBLE)          AS importe_fallido,

  -- Condiciones
  TRY_CAST(TermInMonths AS INTEGER)                  AS plazo_meses,
  LoanStatus                                         AS estado,
  RevolverStatus                                     AS revolvente,
  ProcessingMethod                                   AS metodo_proceso,
  CollateralInd                                      AS con_garantia_real,

  -- Cortes del análisis
  NaicsCode                                          AS naics,
  NaicsDescription                                   AS naics_descripcion,
  ProjectState                                       AS estado_proyecto,
  BusinessType                                       AS tipo_negocio,
  BusinessAge                                        AS edad_negocio,

  -- Prestamista. `banco_actual` es el tenedor de hoy, no el originador: el propio diccionario
  -- dice "currently assigned to". Se carga para poder describirlo, no para cortar por él.
  LocationID                                         AS lender_id,
  BankName                                           AS banco_actual

  /* Deliberadamente NO se cargan: BorrName, BorrStreet, BorrCity, BorrZip, BankStreet,
     BankCity, BankZip, BankFDICNumber, BankNCUANumber, FranchiseCode, FranchiseName,
     ProjectCounty, CongressionalDistrict, SBADistrictOffice, JobsSupported, SoldSecMrktInd,
     InitialInterestRate, FixedorVariableInterestInd, Program, BorrState.

     Los cuatro primeros identifican al prestatario y el caso no los necesita: no cargarlos es
     más fuerte que cargarlos y prometer no usarlos. El resto son columnas que el análisis no
     toca — InitialInterestRate está vacía en el 51% y no aguanta un corte por precio, y Program
     es constante porque los archivos del 504 no se descargaron. */

FROM read_csv(getvariable('ruta_crudos'), all_varchar = true, filename = true);
