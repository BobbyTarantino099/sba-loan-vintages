"""Fase 4 — el análisis: la matriz añada x edad y la proyección de la pérdida terminal.

Lee la base construida por procesar.py, ejecuta consultas/03_curvas.sql y 04_proyeccion.sql,
imprime la descriptiva y exporta a salidas/tablas/ solo lo que la fase 5 y el sitio necesitan.
Únicamente cruzan agregados: nada de datos crudos ni intermedios.

El horizonte terminal H no está codificado a mano. Se deriva aquí de la regla que se escribió
antes de mirarlo: la edad a la que las cohortes completas ya han realizado el 95 % de sus
fallidos. Que la regla mande sobre el número, y no al revés, es lo que impide elegir el
horizonte que mejor le venga a la conclusión.

Uso:  python notebooks/analizar.py
"""

import duckdb
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BD = BASE / 'datos' / 'limpios' / 'sba-loan-vintages.duckdb'
CONSULTAS = BASE / 'consultas'
TABLAS = BASE / 'salidas' / 'tablas'

# Los tres cortes de edad comun, fijados en el plan ANTES de ver ningun resultado.
CORTES = (36, 60, 84)

# Regla del horizonte, escrita antes de calcularlo.
UMBRAL_REALIZACION = 0.95
# Cohortes indiscutiblemente completas bajo cualquier candidato a H, usadas solo para derivarlo.
EDAD_REFERENCIA = 240


def log(titulo):
    print('\n' + '=' * 78)
    print(titulo)
    print('=' * 78)


def derivar_horizonte(con):
    """La edad a la que la cohorte mediana de las mas viejas lleva ya el 95% de sus fallidos.

    Se mide contra los fallidos a EDAD_REFERENCIA meses, no contra "todos", porque "todos"
    incluiria fallidos a 30 anos que ninguna cohorte joven podra alcanzar jamas y estiraria
    el horizonte sin que eso ayude a proyectar nada.
    """
    df = con.sql(f"""
        WITH viejas AS (
          SELECT cohorte FROM cohortes WHERE edad_min_observable >= {EDAD_REFERENCIA}),
        realizado AS (
          SELECT c.cohorte, c.edad,
                 c.fallidos_acum / max(c.fallidos_acum) FILTER (WHERE c.edad = {EDAD_REFERENCIA})
                                      OVER (PARTITION BY c.cohorte) AS fraccion
          FROM curvas c JOIN viejas USING (cohorte)
          WHERE c.dimension = 'global' AND c.nivel = 'todos' AND c.edad <= {EDAD_REFERENCIA})
        SELECT edad, median(fraccion) AS fraccion_mediana
        FROM realizado GROUP BY edad ORDER BY edad
    """).df()
    alcanza = df[df.fraccion_mediana >= UMBRAL_REALIZACION]
    horizonte = int(alcanza.edad.iloc[0])
    print(f'Regla: la edad a la que la cohorte mediana de FY1991-FY2005 lleva el '
          f'{UMBRAL_REALIZACION:.0%} de sus fallidos a {EDAD_REFERENCIA} meses.')
    print(df[df.edad.isin([36, 60, 84, 108, 120, 132, 144, 156, 180])]
            .assign(fraccion_mediana=lambda d: (100 * d.fraccion_mediana).round(1))
            .to_string(index=False))
    print(f'\n-> HORIZONTE TERMINAL H = {horizonte} meses')
    return horizonte


def main():
    TABLAS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(BD))

    con.execute((CONSULTAS / '03_curvas.sql').read_text(encoding='utf-8'))

    log('Descriptiva de las cohortes')
    print(con.sql("""
        SELECT count(*) AS cohortes, min(cohorte) AS desde, max(cohorte) AS hasta,
               sum(en_riesgo) AS en_riesgo, sum(fallidos_totales) AS fallidos,
               round(100.0*sum(fallidos_totales)/sum(en_riesgo), 2) AS tasa_global_pct,
               min(en_riesgo) AS cohorte_menor, max(en_riesgo) AS cohorte_mayor
        FROM cohortes""").df().to_string(index=False))

    log('Edad al fallido: cuando ocurre realmente la perdida')
    print('Solo cohortes con >= 240 meses observables, para que la respuesta no este censurada.')
    print(con.sql("""
        SELECT quantile_cont(edad_al_fallido, 0.25) AS p25,
               median(edad_al_fallido)              AS mediana,
               quantile_cont(edad_al_fallido, 0.75) AS p75,
               quantile_cont(edad_al_fallido, 0.95) AS p95
        FROM prestamos
        WHERE fallido AND NOT fallido_sin_fecha_util
          AND cohorte IN (SELECT cohorte FROM cohortes WHERE edad_min_observable >= 240)
    """).df().to_string(index=False))

    log('Derivacion del horizonte terminal')
    horizonte = derivar_horizonte(con)
    con.execute(f"SET VARIABLE horizonte = {horizonte}")
    con.execute((CONSULTAS / '04_proyeccion.sql').read_text(encoding='utf-8'))

    log('Cohortes completas segun ese horizonte')
    print(con.sql("""
        SELECT count(*) FILTER (WHERE completa) AS completas,
               count(*) FILTER (WHERE NOT completa) AS inmaduras,
               max(cohorte) FILTER (WHERE completa) AS ultima_completa
        FROM proyeccion_terminal""").df().to_string(index=False))

    # ---------------------------------------------------------------
    # Ingenuo contra corregido: la figura 1
    # ---------------------------------------------------------------
    log('Ranking ingenuo contra ranking corregido')
    cortes_sql = ', '.join(str(c) for c in CORTES)
    con.execute(f"""
      CREATE OR REPLACE TABLE ranking AS
      WITH corregido AS (
        SELECT cohorte, edad, tasa_acum_pct, observable
        FROM curvas WHERE dimension = 'global' AND nivel = 'todos' AND edad IN ({cortes_sql}))
      SELECT co.cohorte, co.en_riesgo, co.tasa_cruda_pct,
             max(CASE WHEN c.edad = {CORTES[0]} AND c.observable THEN c.tasa_acum_pct END) AS tasa_{CORTES[0]}m,
             max(CASE WHEN c.edad = {CORTES[1]} AND c.observable THEN c.tasa_acum_pct END) AS tasa_{CORTES[1]}m,
             max(CASE WHEN c.edad = {CORTES[2]} AND c.observable THEN c.tasa_acum_pct END) AS tasa_{CORTES[2]}m
      FROM cohortes co LEFT JOIN corregido c USING (cohorte)
      GROUP BY 1, 2, 3 ORDER BY 1
    """)
    print(con.sql(f"""
        SELECT 'cruda' AS metrica, string_agg(cohorte::VARCHAR, ' ' ORDER BY tasa_cruda_pct DESC) AS peores_5
        FROM (SELECT * FROM ranking ORDER BY tasa_cruda_pct DESC LIMIT 5)
        UNION ALL
        SELECT 'a {CORTES[1]} meses', string_agg(cohorte::VARCHAR, ' ' ORDER BY tasa_{CORTES[1]}m DESC)
        FROM (SELECT * FROM ranking WHERE tasa_{CORTES[1]}m IS NOT NULL
              ORDER BY tasa_{CORTES[1]}m DESC LIMIT 5)
    """).df().to_string(index=False))
    print()
    print(con.sql(f"""
        SELECT cohorte, en_riesgo, tasa_cruda_pct, tasa_{CORTES[0]}m, tasa_{CORTES[1]}m, tasa_{CORTES[2]}m
        FROM ranking ORDER BY cohorte DESC LIMIT 12""").df().to_string(index=False))

    log('Proyeccion de las cohortes inmaduras')
    print(con.sql("""
        SELECT cohorte, edad_lectura, tasa_cruda_pct, tasa_observada,
               factor_mediano, terminal_proyectado_pct, terminal_q1_pct, terminal_q3_pct
        FROM proyeccion_terminal WHERE NOT completa ORDER BY cohorte""").df().to_string(index=False))

    # ---------------------------------------------------------------
    # Exportación: solo agregados
    # ---------------------------------------------------------------
    log('Exportacion a salidas/tablas/')
    # Las curvas viajan sin `en_riesgo` ni `fallidos_acum`: el primero es constante por
    # cohorte x nivel y vive en poblacion_por_nivel.csv, y el segundo se reconstruye de la tasa.
    # Repetirlos en cada fila multiplicaba el peso del explorador por tres a cambio de nada.
    EXPORTES = {
        # La rejilla del explorador: 0-120 meses cada 3, y solo lo que es legible.
        'curva_global.csv': """SELECT cohorte, edad, tasa_acum_pct
                               FROM curvas WHERE dimension='global' AND edad <= 120 AND observable
                               ORDER BY cohorte, edad""",
        'curva_por_plazo.csv': """SELECT cohorte, nivel AS tramo_plazo, edad, tasa_acum_pct
                                  FROM curvas WHERE dimension='plazo' AND edad <= 120 AND observable
                                  ORDER BY cohorte, nivel, edad""",
        'curva_por_importe.csv': """SELECT cohorte, nivel AS tramo_importe, edad, tasa_acum_pct
                                    FROM curvas WHERE dimension='importe' AND edad <= 120 AND observable
                                    ORDER BY cohorte, nivel, edad""",

        # El sector NO entra al explorador: 21 categorias que nadie compara de a 21. Va a figura
        # estatica, y para eso basta con las tres edades de corte, no con la rejilla entera.
        f'curva_por_sector.csv': f"""SELECT cohorte, nivel AS sector, edad, en_riesgo, tasa_acum_pct
                                     FROM curvas
                                     WHERE dimension='sector' AND observable
                                       AND edad IN ({cortes_sql})
                                     ORDER BY cohorte, nivel, edad""",

        'poblacion_por_nivel.csv': """SELECT DISTINCT cohorte, dimension, nivel, en_riesgo
                                      FROM curvas ORDER BY dimension, cohorte, nivel""",
        'ranking_ingenuo_vs_corregido.csv': 'SELECT * FROM ranking ORDER BY cohorte',
        'proyeccion_terminal.csv': 'SELECT * FROM proyeccion_terminal ORDER BY cohorte',
        'factores_desarrollo.csv': 'SELECT * FROM factores_desarrollo ORDER BY edad',
        'cohortes.csv': 'SELECT * FROM cohortes ORDER BY cohorte',
    }
    for nombre, sql in EXPORTES.items():
        destino = TABLAS / nombre
        con.execute(f"COPY ({sql}) TO '{destino.as_posix()}' (HEADER, DELIMITER ',')")
        print(f'{nombre:38s} {destino.stat().st_size / 1024:8.1f} KB')

    total_kb = sum(f.stat().st_size for f in TABLAS.glob('*.csv')) / 1024
    print(f'\nTOTAL {total_kb:.1f} KB')
    if total_kb > 1024:
        print('AVISO: pasa de 1 MB. La agregacion esta incompleta: resumir mas, no subirle')
        print('       el peso al sitio.')

    con.close()


if __name__ == '__main__':
    main()
