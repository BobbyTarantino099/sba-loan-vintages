"""Fase 4 — las verificaciones del análisis.

Cada bloque puede tumbar un hallazgo. Se ejecutan después de analizar.py y su salida se
transcribe a CASO.md: un hallazgo sin verificación registrada no llega a la fase 5.

Uso:  python notebooks/verificar.py
"""

import duckdb
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BD = BASE / 'datos' / 'limpios' / 'sba-loan-vintages.duckdb'
CRUDOS = BASE / 'datos' / 'crudos'

CORTES = (36, 60, 84)
TOPE_PROGRAMA_USD = 5_000_000    # tope legal del 7(a), regla publicada del programa


def spearman(a, b):
    """Correlacion de rangos sin scipy.

    pandas delega `.corr(method='spearman')` en scipy, que no esta en requirements.txt y no
    merece estarlo por una sola formula. Spearman ES Pearson sobre los rangos, asi que se
    calcula asi y el caso mantiene sus cuatro dependencias.
    """
    return a.rank().corr(b.rank())


def log(titulo):
    print('\n' + '=' * 78)
    print(titulo)
    print('=' * 78)


def main():
    con = duckdb.connect(str(BD), read_only=True)
    pd.set_option('display.width', 200)

    # ---------------------------------------------------------------
    # V0 - Los 180 fallidos con importe cero
    # ---------------------------------------------------------------
    log('V0 - Fallidos con importe de fallido cero: repartidos o concentrados?')
    print('V2 depende de esto. Si se concentran en pocas cohortes, la metrica en dolares no se')
    print('puede leer tal cual en esas cohortes.\n')
    print(con.sql("""
        WITH z AS (
          SELECT cohorte, count(*) AS cero
          FROM prestamos WHERE fallido AND coalesce(importe_fallido, 0) = 0
          GROUP BY 1)
        SELECT count(*) AS cohortes_afectadas, sum(cero) AS total_cero,
               max(cero) AS max_en_una_cohorte,
               round(100.0 * max(cero) / sum(cero), 1) AS pct_en_la_peor
        FROM z""").df().to_string(index=False))
    print()
    print(con.sql("""
        SELECT p.cohorte, count(*) FILTER (WHERE p.fallido AND coalesce(p.importe_fallido,0)=0) AS cero,
               count(*) FILTER (WHERE p.fallido) AS fallidos,
               round(100.0 * count(*) FILTER (WHERE p.fallido AND coalesce(p.importe_fallido,0)=0)
                     / nullif(count(*) FILTER (WHERE p.fallido), 0), 2) AS pct_de_los_fallidos
        FROM prestamos p GROUP BY 1
        HAVING count(*) FILTER (WHERE p.fallido AND coalesce(p.importe_fallido,0)=0) > 0
        ORDER BY cero DESC LIMIT 8""").df().to_string(index=False))

    # ---------------------------------------------------------------
    # V1 - Sensatez
    # ---------------------------------------------------------------
    log('V1 - Sensatez: recuento por una via independiente y reglas del programa')
    print('El pipeline cuenta sobre la tabla `prestamos`. Aqui se recuenta leyendo los CSV crudos')
    print('directamente, sin pasar por ninguna tabla intermedia. Si difieren, hay un bug.\n')
    glob = (CRUDOS / 'sba_7a_*_2026-06-30.csv').as_posix()
    directo = con.sql(f"""
        SELECT count(*) AS aprobaciones,
               count(*) FILTER (WHERE LoanStatus IN ('P I F','CHGOFF','EXEMPT')) AS desembolsados,
               count(*) FILTER (WHERE LoanStatus = 'CHGOFF') AS fallidos
        FROM read_csv('{glob}', all_varchar = true)""").fetchone()
    pipeline = con.sql("""
        SELECT (SELECT count(*) FROM raw_7a),
               (SELECT count(*) FROM raw_7a WHERE estado IN ('P I F','CHGOFF','EXEMPT')),
               (SELECT count(*) FROM raw_7a WHERE estado = 'CHGOFF')""").fetchone()
    for etiqueta, a, b in zip(('aprobaciones', 'desembolsados', 'fallidos'), directo, pipeline):
        print(f'{etiqueta:16s} crudo={a:>10,}  pipeline={b:>10,}  '
              f'{"OK" if a == b else "DISCREPANCIA"}')

    print('\nReglas publicadas del programa 7(a):')
    reglas = con.sql(f"""
        SELECT max(importe_aprobado) AS importe_max,
               count(*) FILTER (WHERE importe_aprobado > {TOPE_PROGRAMA_USD}) AS sobre_el_tope,
               count(*) FILTER (WHERE importe_garantizado > importe_aprobado) AS garantia_mayor_que_prestamo,
               round(100.0 * sum(importe_garantizado) / sum(importe_aprobado), 1) AS pct_garantizado_medio
        FROM prestamos""").df()
    print(reglas.to_string(index=False))
    print(f'El tope legal del 7(a) son {TOPE_PROGRAMA_USD:,} USD. Ningun prestamo deberia superarlo,')
    print('y ninguna garantia deberia exceder su propio prestamo.')
    print('\nLIMITACION DECLARADA: la reconciliacion contra las tablas de desempeno que la SBA')
    print('publica aparte no se pudo completar — el enlace al archivo (WebsiteReports_FY25Q3.zip)')
    print('devuelve 404 a fecha de 2026-09-01. Queda como verificacion externa pendiente, no como')
    print('verificacion hecha.')

    # ---------------------------------------------------------------
    # V2 - Conteo contra dolares
    # ---------------------------------------------------------------
    log('V2 - La curva ponderada por dolares apunta en la misma direccion?')
    v2 = con.sql(f"""
        SELECT cohorte, tasa_acum_pct AS por_conteo, tasa_acum_usd_pct AS por_dolares
        FROM curvas
        WHERE dimension = 'global' AND nivel = 'todos' AND edad = {CORTES[1]} AND observable
        ORDER BY cohorte""").df()
    r = spearman(v2.por_conteo, v2.por_dolares)
    print(v2.tail(10).to_string(index=False))
    print(f'\nCohortes comparadas: {len(v2)}')
    print(f'Correlacion de rangos (Spearman) conteo vs dolares a {CORTES[1]} meses: {r:.4f}')
    print('Cerca de 1 = el hallazgo es sobre la anada, no sobre el tamano del prestamo.')

    # ---------------------------------------------------------------
    # V3 - CARES Act seccion 1112
    # ---------------------------------------------------------------
    log('V3 - CARES Act 1112: se aplano la curva temprana de FY2020-21 por politica?')
    print('El gobierno pago cuotas de muchos 7(a) durante la pandemia. Si esas cohortes tienen la')
    print('curva temprana mas plana que sus vecinas A IGUAL EDAD, la causa puede ser politica y no')
    print('calidad crediticia, y hay que decirlo antes de compararlas.\n')
    print(con.sql("""
        SELECT edad,
               max(CASE WHEN cohorte=2018 THEN tasa_acum_pct END) AS fy2018,
               max(CASE WHEN cohorte=2019 THEN tasa_acum_pct END) AS fy2019,
               max(CASE WHEN cohorte=2020 THEN tasa_acum_pct END) AS fy2020,
               max(CASE WHEN cohorte=2021 THEN tasa_acum_pct END) AS fy2021,
               max(CASE WHEN cohorte=2022 THEN tasa_acum_pct END) AS fy2022
        FROM curvas
        WHERE dimension='global' AND nivel='todos' AND observable
          AND cohorte BETWEEN 2018 AND 2022 AND edad IN (12,24,36,45)
        GROUP BY edad ORDER BY edad""").df().to_string(index=False))

    # ---------------------------------------------------------------
    # V4 - Anada o mezcla?
    # ---------------------------------------------------------------
    log('V4 - La explicacion alternativa: es la anada o es la mezcla?')
    print('La composicion por plazo y tamano cambia entre anos. Aqui se estandariza directamente:')
    print('se aplica a cada cohorte la MISMA mezcla de referencia (la del conjunto) sobre sus')
    print('propias tasas por estrato. Si el orden se mantiene, el hallazgo es de la anada.\n')
    v4 = con.sql(f"""
        WITH estratos AS (
          SELECT cohorte, tramo_plazo, tramo_importe,
                 count(*) AS n,
                 count(*) FILTER (WHERE fallido AND NOT fallido_sin_fecha_util
                                    AND edad_al_fallido <= {CORTES[0]}) AS eventos
          FROM prestamos
          WHERE NOT cohorte_parcial AND edad_observable >= {CORTES[0]}
          GROUP BY 1,2,3),
        pesos AS (
          SELECT tramo_plazo, tramo_importe, sum(n) AS peso FROM estratos GROUP BY 1,2),
        total AS (SELECT sum(peso) AS w FROM pesos)
        SELECT e.cohorte,
               round(100.0 * sum(e.eventos) / sum(e.n), 4)                        AS cruda_36m,
               round(100.0 * sum((1.0*e.eventos/e.n) * p.peso) / max(t.w), 4)      AS estandarizada_36m
        FROM estratos e JOIN pesos p USING (tramo_plazo, tramo_importe) CROSS JOIN total t
        GROUP BY e.cohorte ORDER BY e.cohorte""").df()
    r4 = spearman(v4.cruda_36m, v4.estandarizada_36m)
    print(v4.tail(12).to_string(index=False))
    print(f'\nCorrelacion de rangos entre la tasa a {CORTES[0]} meses y su version estandarizada '
          f'por mezcla: {r4:.4f}')
    print('Cerca de 1 = la reordenacion NO la produce el cambio de composicion.')

    # ---------------------------------------------------------------
    # V5 - Sensibilidad al corte n*
    # ---------------------------------------------------------------
    log('V5 - Depende la conclusion del corte de edad elegido?')
    v5 = con.sql(f"""
        SELECT cohorte,
               max(CASE WHEN edad={CORTES[0]} THEN tasa_acum_pct END) AS m36,
               max(CASE WHEN edad={CORTES[1]} THEN tasa_acum_pct END) AS m60,
               max(CASE WHEN edad={CORTES[2]} THEN tasa_acum_pct END) AS m84
        FROM curvas WHERE dimension='global' AND nivel='todos' AND observable
        GROUP BY cohorte ORDER BY cohorte""").df()
    comun = v5.dropna()
    print(f'Cohortes con los tres cortes observables: {len(comun)}')
    print('Correlacion de rangos entre cortes:')
    for a, b in (('m36', 'm60'), ('m36', 'm84'), ('m60', 'm84')):
        print(f'  {a} vs {b}: {spearman(comun[a], comun[b]):.4f}')
    print('\nPeores 5 cohortes segun cada corte:')
    for c in ('m36', 'm60', 'm84'):
        peores = v5.dropna(subset=[c]).nlargest(5, c).cohorte.tolist()
        print(f'  {c}: {peores}')

    # ---------------------------------------------------------------
    # V6 - Recalculo por otra via
    # ---------------------------------------------------------------
    log('V6 - Recalculo del acumulado por un camino distinto')
    print('La curva se construye con una suma de ventana sobre eventos agrupados en la rejilla.')
    print('Aqui se recalcula contando directamente los prestamos con edad_al_fallido <= edad,')
    print('sin ventana y sin rejilla. Cualquier diferencia es un bug, no un hallazgo.\n')
    v6 = con.sql(f"""
        WITH directo AS (
          SELECT c.cohorte, g.edad,
                 count(*) FILTER (WHERE p.fallido AND NOT p.fallido_sin_fecha_util
                                    AND p.edad_al_fallido <= g.edad) AS fallidos_directo,
                 count(*) AS en_riesgo
          FROM prestamos p
          JOIN cohortes c USING (cohorte)
          CROSS JOIN (SELECT unnest([{', '.join(str(c) for c in CORTES)}, 120]) AS edad) g
          WHERE NOT p.cohorte_parcial
          GROUP BY 1, 2)
        SELECT count(*) AS celdas_comparadas,
               count(*) FILTER (WHERE d.fallidos_directo <> cu.fallidos_acum) AS discrepancias,
               max(abs(round(100.0*d.fallidos_directo/d.en_riesgo, 4) - cu.tasa_acum_pct)) AS max_dif_pct
        FROM directo d
        JOIN curvas cu ON cu.cohorte=d.cohorte AND cu.edad=d.edad
                      AND cu.dimension='global' AND cu.nivel='todos'""").df()
    print(v6.to_string(index=False))
    if int(v6.discrepancias.iloc[0]) != 0:
        raise SystemExit('V6 no cuadra: la curva no reproduce el recuento directo. Hay un bug.')
    print('\nV6 OK: los dos caminos dan el mismo acumulado.')

    con.close()


if __name__ == '__main__':
    main()
