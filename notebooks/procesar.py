"""Fase 3 — construye la base del caso desde los crudos congelados.

Ejecuta consultas/01_construir_base.sql y consultas/02_poblacion.sql sobre DuckDB, imprime la
reconciliación de conteos de cada transformación y comprueba que el resultado sigue siendo el
que cerró la fase 2. Si esa comprobación falla, algo se rompió: el pipeline no se da por bueno
porque termine sin error.

Este script no transforma nada por su cuenta. Toda la lógica está en los .sql, que es donde se
puede leer y auditar; aquí solo se resuelven rutas y se cuentan filas.

Uso:  python notebooks/procesar.py
"""

import duckdb
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CRUDOS = BASE / 'datos' / 'crudos'
LIMPIOS = BASE / 'datos' / 'limpios'
CONSULTAS = BASE / 'consultas'

FECHA_CORTE = '2026-06-30'
GLOB_CRUDOS = f'sba_7a_*_{FECHA_CORTE}.csv'

# Lo que cerró la fase 2, medido sobre los crudos antes de escribir una sola transformación.
# Están en CASO.md sección 2 y en documentacion/fichas-de-fuente.md. Si el pipeline no las
# reproduce, el filtro cambió sin que nadie lo decidiera.
ESPERADO = {
    'aprobaciones':        1961455,
    'poblacion_en_riesgo':  1697542,   # antes de descartar los 3 importes <= 0
    'fallidos':             220688,
    'fallidos_con_fecha':   220630,   # en el crudo; 32 tienen fecha posterior al corte y no entran en la curva
    'cancelados':           242790,
    'no_desembolsados':      21123,
}


def registrar(titulo, **kv):
    print(f'--- {titulo} ---')
    for k, v in kv.items():
        print(f'{k}: {v:,}' if isinstance(v, int) else f'{k}: {v}')
    print()


def main():
    LIMPIOS.mkdir(parents=True, exist_ok=True)
    destino = LIMPIOS / 'sba-loan-vintages.duckdb'
    destino.unlink(missing_ok=True)   # desde cero: un pipeline que reusa estado no es reproducible

    con = duckdb.connect(str(destino))
    con.execute(f"SET VARIABLE ruta_crudos = '{(CRUDOS / GLOB_CRUDOS).as_posix()}'")

    def uno(sql):
        return con.sql(sql).fetchone()[0]

    # =========================================================
    # T1 — Carga fiel del crudo
    # =========================================================
    con.execute((CONSULTAS / '01_construir_base.sql').read_text(encoding='utf-8'))

    n_crudo = uno('SELECT count(*) FROM raw_7a')
    registrar('T1 - Carga del crudo, sin transformar',
              aprobaciones=n_crudo,
              archivos=uno('SELECT count(DISTINCT archivo_origen) FROM raw_7a'),
              fecha_corte=str(uno('SELECT max(fecha_corte) FROM raw_7a')))

    # Los cuatro archivos deben particionar los años fiscales sin solaparse: si un año apareciera
    # en dos archivos, cada préstamo de ese año contaría dos veces y la cohorte saldría inflada
    # sin que ninguna otra comprobación lo notase.
    solapes = uno("""SELECT count(*) FROM (
                       SELECT anio_fiscal FROM raw_7a
                       GROUP BY anio_fiscal HAVING count(DISTINCT archivo_origen) > 1)""")
    registrar('Particion por archivo', anios_en_mas_de_un_archivo=solapes,
              solapa='no' if solapes == 0 else 'SI - revisar antes de seguir')
    if solapes:
        raise SystemExit('Los archivos se solapan por anio fiscal: las cohortes estarian duplicadas.')

    # Un unico AsOfDate: si hubiera dos, la censura no estaria en el mismo punto para todos.
    n_cortes = uno('SELECT count(DISTINCT fecha_corte) FROM raw_7a')
    if n_cortes != 1:
        raise SystemExit(f'Hay {n_cortes} fechas de corte distintas: la censura no seria comparable.')

    # Casteo sin perdidas: TRY_CAST devuelve NULL en vez de fallar, asi que hay que mirarlo.
    registrar('Perdidas por casteo (deben ser 0)',
              fechas_aprobacion=uno('SELECT count(*) FROM raw_7a WHERE fecha_aprobacion IS NULL'),
              importes=uno('SELECT count(*) FROM raw_7a WHERE importe_aprobado IS NULL'),
              plazos=uno('SELECT count(*) FROM raw_7a WHERE plazo_meses IS NULL'))

    # =========================================================
    # T2-T3 — Reconciliación: aprobaciones menos excluidas igual a población
    # =========================================================
    n_cancelados = uno("SELECT count(*) FROM raw_7a WHERE estado = 'CANCLD'")
    n_no_desemb = uno("SELECT count(*) FROM raw_7a WHERE estado = 'COMMIT'")
    n_riesgo = uno("SELECT count(*) FROM raw_7a WHERE estado IN ('P I F','CHGOFF','EXEMPT')")
    n_importe_malo = uno("""SELECT count(*) FROM raw_7a
                            WHERE estado IN ('P I F','CHGOFF','EXEMPT') AND importe_aprobado <= 0""")

    con.execute((CONSULTAS / '02_poblacion.sql').read_text(encoding='utf-8'))
    n_final = uno('SELECT count(*) FROM prestamos')

    registrar('T2 - Fuera lo que nunca se desembolso',
              antes=n_crudo, excluidas=n_cancelados + n_no_desemb, despues=n_riesgo,
              cancelados=n_cancelados, no_desembolsados=n_no_desemb,
              motivo='sin desembolso no hay dinero en riesgo: ni numerador ni denominador')
    registrar('T3 - Fuera los importes no positivos',
              antes=n_riesgo, excluidas=n_importe_malo, despues=n_final,
              motivo='3 filas, una en -120.000 USD: ruido, pero se cuenta')

    cuadra = (n_crudo - n_cancelados - n_no_desemb - n_importe_malo) == n_final
    registrar('Reconciliacion de conteos', cuadra=cuadra)
    if not cuadra:
        raise SystemExit('La reconciliacion no cuadra: hay filas perdidas sin decision asociada.')

    # =========================================================
    # T4 — Etiquetado: nada se pierde, todo queda clasificado
    # =========================================================
    registrar('T4 - Etiquetado de la poblacion',
              filas=n_final,
              fallidos=uno('SELECT count(*) FROM prestamos WHERE fallido'),
              fallidos_sin_fecha_util=uno('SELECT count(*) FROM prestamos WHERE fallido_sin_fecha_util'),
              fallidos_en_la_curva=uno('SELECT count(*) FROM prestamos WHERE fallido AND NOT fallido_sin_fecha_util'),
              vivos_exempt=uno("SELECT count(*) FROM prestamos WHERE estado = 'EXEMPT'"),
              plazo_unknown=uno("SELECT count(*) FROM prestamos WHERE tramo_plazo = 'unknown'"),
              sector_unknown=uno("SELECT count(*) FROM prestamos WHERE sector = 'unknown'"),
              cohorte_parcial=uno('SELECT count(*) FROM prestamos WHERE cohorte_parcial'))

    # Ninguna fila puede quedarse sin tramo: un NULL aqui se convierte en una barra que falta
    # en el grafico y en un total que no suma.
    sin_etiqueta = uno("""SELECT count(*) FROM prestamos
                          WHERE tramo_plazo IS NULL OR tramo_importe IS NULL OR sector IS NULL
                             OR cohorte IS NULL OR edad_observable IS NULL""")
    registrar('Filas sin etiquetar (deben ser 0)', sin_etiqueta=sin_etiqueta)
    if sin_etiqueta:
        raise SystemExit('Hay filas sin etiquetar: los cortes no sumarian el total.')

    # La edad al fallido nunca puede ser negativa ni exceder lo observable.
    imposibles = uno("""SELECT count(*) FROM prestamos
                        WHERE fallido AND NOT fallido_sin_fecha_util
                          AND (edad_al_fallido IS NULL
                               OR edad_al_fallido < 0
                               OR edad_al_fallido > edad_observable)""")
    registrar('Edades imposibles (deben ser 0)', imposibles=imposibles)
    if imposibles:
        raise SystemExit('Hay fallidos anteriores a su aprobacion o posteriores al corte.')

    # =========================================================
    # Sensibilidad de los duplicados que NO se eliminaron
    # =========================================================
    # 403 grupos son identicos en las 42 columnas del crudo (519 filas sobrantes). No se
    # deduplican porque el archivo no trae numero de prestamo y la mayoria de las coincidencias
    # son prestamos distintos; se acota aqui cuanto podrian mover la tasa en el peor caso.
    tasa = uno('SELECT 100.0 * count(*) FILTER (WHERE fallido) / count(*) FROM prestamos')
    registrar('Cota de los duplicados no eliminados',
              filas_sobrantes_identicas=519,
              pct_de_la_poblacion=round(100 * 519 / n_final, 4),
              tasa_fallidos_pct=round(tasa, 3),
              cota='si las 519 fueran todas fallidos falsos, la tasa se moveria < 0,04 pp')

    # =========================================================
    # Regresión contra el cierre de la fase 2
    # =========================================================
    obtenido = {
        'aprobaciones':        n_crudo,
        'poblacion_en_riesgo': n_riesgo,
        'fallidos':            uno("SELECT count(*) FROM raw_7a WHERE estado = 'CHGOFF'"),
        'fallidos_con_fecha':  uno("""SELECT count(*) FROM raw_7a
                                      WHERE estado = 'CHGOFF' AND fecha_fallido IS NOT NULL"""),
        'cancelados':          n_cancelados,
        'no_desembolsados':    n_no_desemb,
    }
    fallos = {k: (v, obtenido[k]) for k, v in ESPERADO.items() if obtenido[k] != v}
    registrar('Regresion contra el cierre de la fase 2',
              esperado=ESPERADO, obtenido=obtenido,
              resultado='OK' if not fallos else f'DISCREPANCIA en {fallos}')

    con.close()
    if fallos:
        raise SystemExit('El pipeline no reproduce los numeros de la fase 2. Revisar antes de seguir.')
    print(f'Base construida en {destino.relative_to(BASE)}')


if __name__ == '__main__':
    main()
