"""Fase 5 — las figuras del caso.

Cuatro figuras, una por hallazgo, con el titular que enuncia el hallazgo y no el tema.

Tres decisiones deliberadas de este caso:

  · **Tema propio.** Carmesí y cian, frente al azul y naranja del caso 1 y el verde y violeta
    del caso 2. Los tonos ocupados por los casos anteriores se midieron en OKLCh (38°, 152°,
    255°, 303°) y este ocupa dos huecos reales: 17° y 213°. La paleta pasa el verificador de la
    skill `dataviz` — banda de luminosidad, suelo de croma, ΔE 16,5 deutan y 32,5 tritan sobre
    un objetivo de 8, contraste — y la rampa, la monotonicidad de luminancia. La composición no
    se toca: es lo que hace que los tres casos se reconozcan como un mismo cuerpo de trabajo.

  · **Ninguna forma repetida.** El caso 1 gastó dumbbell, tabla-matriz, lollipop y barras
    agrupadas; el caso 2, curva de concentración, líneas, barras divergentes, slope y apiladas
    al 100 %. Aquí: columnas apiladas en absoluto con bigote, curva de escalones, bump chart y
    small multiples. Adaptar la forma al dato es parte del oficio que el portafolio demuestra.

  · **La rejilla de paneles de la F4 se implementa aquí, no en estilo.py.** El motor de estilo
    es compartido por los tres casos y no se bifurca por una necesidad de uno solo. Si un
    segundo caso pide small multiples, entonces se promueve a estilo.py — en la plantilla, no
    en la copia.

Uso:  python notebooks/graficos.py   (requiere procesar.py y analizar.py antes)
"""

import json
import sys
from pathlib import Path

import duckdb
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
BD = BASE / 'datos' / 'limpios' / 'sba-loan-vintages.duckdb'
GRAFICOS = BASE / 'salidas' / 'graficos'
TABLAS = BASE / 'salidas' / 'tablas'

FUENTE = 'SBA 7(a) FOIA loan-level data, as of 2026-06-30 (U.S. Government Works)'

estilo.aplicar(
    acento='#a8203a',
    contra='#0e8ea8',
    rampa=['#fbe9ec', '#f3c6ce', '#e08fa0', '#c4526a', '#a8203a'],
)

con = duckdb.connect(str(BD), read_only=True)


def tabla(sql):
    return con.sql(sql).df()


def paneles(fig, ax, filas, columnas, hgap=0.055, vgap=0.16, aire_titulo=0.055):
    """Sustituye el eje único de estilo.figura() por una rejilla, en su mismo rectángulo.

    Se hace así para conservar la cabecera de tres niveles, la nota de fuente y la firma,
    que viven fuera de los ejes y son la mitad de la identidad de la figura.
    """
    caja = ax.get_position()
    ax.remove()
    # El titulo de cada panel se dibuja por encima de su eje: si la rejilla ocupa todo el
    # rectangulo, los titulos se meten en la linea de periodo de la cabecera.
    alto_util = caja.height - aire_titulo
    an = (caja.width - hgap * (columnas - 1)) / columnas
    al = (alto_util - vgap * (filas - 1)) / filas
    rejilla = []
    for f in range(filas):
        for c in range(columnas):
            x = caja.x0 + c * (an + hgap)
            y = caja.y0 + (filas - 1 - f) * (al + vgap)
            rejilla.append(fig.add_axes([x, y, an, al]))
    return rejilla


# ===========================================================================
# 1 - El titular: lo que se ve y lo que falta por llegar
# ===========================================================================
# Columnas apiladas en valor absoluto: abajo la pérdida ya realizada -- el número que un
# fondo leería en su informe -- y encima la que todavía no ha aparecido. El bigote es el
# rango intercuartílico de los factores de desarrollo. Las dos añadas más jóvenes no llevan
# parte superior: su factor es 17x y 606x, así que no son proyectables y el hueco rotulado
# ES el mensaje, no una barra que falta.
p = tabla("""
    SELECT cohorte, tasa_cruda_pct, terminal_proyectado_pct, terminal_q1_pct,
           terminal_q3_pct, proyectable
    FROM proyeccion_terminal WHERE cohorte >= 2015 ORDER BY cohorte
""")
ref = tabla("""
    SELECT min(tasa_cruda_pct) AS lo, max(tasa_cruda_pct) AS hi
    FROM cohortes WHERE cohorte BETWEEN 2010 AND 2014
""").iloc[0]

fig, ax = estilo.figura(
    'Corrected for age, the 2023 vintage is on track for 12.2% losses — the worst since 2009',
    'Cumulative charge-off rate of SBA 7(a) loans by fiscal year of approval. The lower block is '
    'the loss already recorded; the upper block is what the maturation of completed vintages '
    'implies is still to come.',
    'FY2015–FY2025 · 1,697,539 disbursed loans · share of loans, not dollars',
    fuente=FUENTE,
    nota='Projection: observed rate x the median development factor of the 24 completed vintages. '
         'Whisker = interquartile range of those factors.',
    figsize=(9.6, 6.8),
)

x = np.arange(len(p))
# El bloque de abajo es lo REGISTRADO A DIA DE HOY (la tasa cruda), no la tasa a la edad de
# lectura: el subtitulo promete "loss already recorded", y la tasa a edad de lectura ignora los
# fallidos de los prestamos aprobados al principio del ano fiscal, que si estan en los libros.
realizado = p.tasa_cruda_pct.to_numpy()
pendiente = np.where(p.proyectable, p.terminal_proyectado_pct - p.tasa_cruda_pct, np.nan)

ax.axhspan(ref.lo, ref.hi, color=estilo.RAMPA[0], zorder=0)
ax.text(len(p) - 0.4, ref.hi, 'FY2010–FY2014 landed here', va='bottom', ha='right',
        color=estilo.TINTA_TENUE, fontsize=8.5)

ax.bar(x, realizado, width=0.62, color=estilo.CONTEXTO, label='Already recorded', zorder=2)
ax.bar(x, pendiente, width=0.62, bottom=realizado, color=estilo.ACENTO,
       label='Still to come (projected)', zorder=2,
       linewidth=1.6, edgecolor=estilo.PAPEL)   # separador de 2px entre segmentos

for i, fila in p.iterrows():
    if fila.proyectable:
        ax.plot([i, i], [fila.terminal_q1_pct, fila.terminal_q3_pct],
                color=estilo.TINTA, linewidth=1.4, zorder=3, solid_capstyle='butt')
        ax.text(i, fila.terminal_q3_pct + 0.35, f'{fila.terminal_proyectado_pct:.1f}',
                ha='center', va='bottom', color=estilo.TINTA, fontsize=9.5)
    else:
        # Las dos jovenes se rotulan a la MISMA altura: desalineadas parecian dos casos
        # distintos y son el mismo. Se anota tambien su tasa cruda, que de otro modo es una
        # barra invisible -- y es justo el numero que un fondo leeria como excelente.
        ax.text(i, 3.0, 'not\nprojectable', ha='center', va='bottom',
                color=estilo.TINTA_TENUE, fontsize=8.5, linespacing=1.25)
        ax.text(i, 1.45, f'raw\n{fila.tasa_cruda_pct:.2f}%', ha='center', va='bottom',
                color=estilo.TINTA_SUAVE, fontsize=8.5, linespacing=1.25)

ax.set_xticks(x)
ax.set_xticklabels([str(c) for c in p.cohorte])
ax.set_ylabel('Cumulative charge-off rate (%)')
ax.set_ylim(0, 15.5)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
estilo.leyenda(ax)
estilo.guardar(fig, GRAFICOS / '01_lo_que_falta_por_llegar.png')


# ===========================================================================
# 2 - El mecanismo: a los tres años solo se ha visto una cuarta parte
# ===========================================================================
# Curva de escalones del porcentaje de la pérdida terminal ya realizado a cada edad,
# medido sobre las 24 añadas completas. Es el motor de todo lo demás: si esta curva
# fuese plana desde el mes 12, la tasa cruda no mentiría.
d = tabla("""
    SELECT edad, round(100.0 / factor_mediano, 2) AS pct
    FROM factores_desarrollo WHERE edad BETWEEN 3 AND 138 ORDER BY edad
""")

fig, ax = estilo.figura(
    'At three years a vintage has shown only a quarter of the losses it will suffer',
    'Share of a vintage’s eventual charge-offs that has already occurred, by months since '
    'approval. Measured on the 24 vintages old enough to be complete.',
    'FY1991–FY2014 · 138-month terminal horizon · median across vintages',
    fuente=FUENTE,
    nota='The horizon is the age at which the median completed vintage has realised 95% of its '
         'charge-offs. Derived, not chosen.',
    figsize=(9.6, 6.4),
)

ax.fill_between(d.edad, d.pct, step='post', color=estilo.RAMPA[0], zorder=1)
ax.step(d.edad, d.pct, where='post', color=estilo.ACENTO, linewidth=2.0, zorder=3)

for edad, etiqueta in [(36, None), (60, None), (120, None)]:
    fila = d[d.edad == edad].iloc[0]
    ax.plot([edad, edad], [0, fila.pct], color=estilo.REGLA, linewidth=1.0, zorder=2)
    ax.plot([edad], [fila.pct], 'o', color=estilo.ACENTO, markersize=7, zorder=4)
    ax.text(edad, fila.pct + 3.5, f'{fila.pct:.1f}%', ha='center', va='bottom',
            color=estilo.TINTA, **estilo._prop('negrita', 10.5))

estilo.anotar(ax, 'Three years in, three quarters\nof the loss is still ahead',
              xy=(36, 23.5), xytexto=(52, 12))

ax.set_xlabel('Months since approval')
ax.set_ylabel('Share of eventual charge-offs already recorded (%)')
ax.set_xlim(0, 140)
ax.set_ylim(0, 105)
ax.set_xticks([0, 12, 24, 36, 48, 60, 84, 120, 138])
ax.yaxis.grid(True)
ax.set_axisbelow(True)
estilo.guardar(fig, GRAFICOS / '02_a_los_tres_anos.png')


# ===========================================================================
# 3 - Nivel, no orden: el ranking apenas se mueve
# ===========================================================================
# Bump chart del rango de cada añada bajo cuatro lecturas. Es la hipótesis contradicha:
# se esperaba que corregir por edad reordenase la tabla, y no lo hace. Lo que corrige es
# el nivel de las añadas jóvenes, no su posición.
r = tabla("""
    SELECT cohorte, tasa_cruda_pct, tasa_36m, tasa_60m, tasa_84m
    FROM ranking
    WHERE tasa_36m IS NOT NULL AND tasa_60m IS NOT NULL AND tasa_84m IS NOT NULL
    ORDER BY cohorte
""")
columnas = ['tasa_cruda_pct', 'tasa_36m', 'tasa_60m', 'tasa_84m']
rangos = r[columnas].rank(ascending=False, method='min')
peores = r.loc[rangos.tasa_60m <= 5, 'cohorte'].tolist()

fig, ax = estilo.figura(
    'Correcting for age changes the level, not the league table: the five worst vintages are the same',
    'Rank of each vintage by cumulative charge-off rate, read four ways: the raw rate, and the '
    'rate at a common age of 36, 60 and 84 months. Rank 1 is the worst.',
    f'{len(r)} vintages with all four readings observable · FY1991–FY2018',
    fuente=FUENTE,
    nota='Rank correlation between readings is 0.92 to 0.96. This contradicts the hypothesis '
         'recorded before the analysis.',
    figsize=(9.6, 6.8),
)

xs = np.arange(4)
for i, fila in r.iterrows():
    destacada = fila.cohorte in peores
    ax.plot(xs, rangos.loc[i, columnas].to_numpy(),
            color=estilo.ACENTO if destacada else '#dedbd2',
            linewidth=2.0 if destacada else 1.1,
            marker='o', markersize=6 if destacada else 3.5,
            zorder=3 if destacada else 1)
    if destacada:
        ax.text(-0.12, rangos.loc[i, 'tasa_cruda_pct'], f'{int(fila.cohorte)}',
                ha='right', va='center', color=estilo.ACENTO, fontsize=9.5)
        ax.text(3.12, rangos.loc[i, 'tasa_84m'], f'{int(fila.cohorte)}',
                ha='left', va='center', color=estilo.ACENTO, fontsize=9.5)

ax.set_xticks(xs)
ax.set_xticklabels(['Raw rate', 'At 36 months', 'At 60 months', 'At 84 months'])
ax.set_xlim(-0.75, 3.75)
ax.invert_yaxis()
ax.set_ylabel('Rank (1 = worst)')
ax.set_yticks([1, 5, 10, 15, 20, 25, 28])
ax.yaxis.grid(True)
ax.set_axisbelow(True)
estilo.guardar(fig, GRAFICOS / '03_nivel_no_orden.png')


# ===========================================================================
# 4 - El artefacto de política: 2020 y 2021 no son buenas añadas
# ===========================================================================
# Small multiples con ejes idénticos en los cinco paneles. Con el eje compartido,
# "misma edad, distinto nivel" se lee sin narración -- y esa es la prueba de que la
# diferencia no es maduración sino la CARES Act pagando las cuotas.
c = tabla("""
    SELECT cohorte, edad, tasa_acum_pct FROM curvas
    WHERE dimension='global' AND nivel='todos' AND observable
      AND cohorte BETWEEN 2018 AND 2022 AND edad <= 45
    ORDER BY cohorte, edad
""")
cohortes = sorted(c.cohorte.unique())
suprimidas = {2020, 2021}

fig, ax = estilo.figura(
    'The 2020 and 2021 vintages default at half the rate of their neighbours — because the '
    'government was paying the instalments',
    'Cumulative charge-off rate over the first 45 months, one panel per vintage, identical axes. '
    'CARES Act section 1112 covered principal and interest on many 7(a) loans through the pandemic.',
    'FY2018–FY2022 · first 45 months · share of loans',
    fuente=FUENTE,
    nota='Read as credit quality, these two vintages would flatter any underwriting model built '
         'on them. They are policy, not performance.',
    figsize=(10.2, 6.0),
)
ejes = paneles(fig, ax, filas=1, columnas=5, hgap=0.022)
techo = c.tasa_acum_pct.max() * 1.22

for eje, cohorte in zip(ejes, cohortes):
    sub = c[c.cohorte == cohorte]
    suprimida = cohorte in suprimidas
    color = estilo.ACENTO if suprimida else estilo.CONTEXTO
    eje.fill_between(sub.edad, sub.tasa_acum_pct,
                     color=estilo.RAMPA[0] if suprimida else '#f2f1ec', zorder=1)
    eje.plot(sub.edad, sub.tasa_acum_pct, color=color,
             linewidth=2.4 if suprimida else 1.4, zorder=3)
    final = sub.iloc[-1]
    eje.text(final.edad, final.tasa_acum_pct + techo * 0.04, f'{final.tasa_acum_pct:.1f}%',
             ha='right', va='bottom', color=color, fontsize=10,
             **estilo._prop('negrita' if suprimida else 'regular', 10))
    # La identidad no se codifica solo con color: los dos paneles afectados van rotulados.
    eje.set_title(f'FY{cohorte}' + ('\nCARES Act relief' if suprimida else ''),
                  color=color, fontsize=10.5, pad=8,
                  **estilo._prop('negrita' if suprimida else 'regular', 10.5))
    eje.set_ylim(0, techo)
    eje.set_xlim(0, 46)
    eje.set_xticks([0, 24, 45])
    eje.yaxis.grid(True)
    eje.set_axisbelow(True)
    if eje is ejes[0]:
        eje.set_ylabel('Cumulative charge-off rate (%)')
    else:
        eje.set_yticklabels([])
ejes[2].set_xlabel('Months since approval')
estilo.guardar(fig, GRAFICOS / '04_artefacto_de_politica.png')


# ===========================================================================
# El JSON del explorador (se consume en la fase 7)
# ===========================================================================
# Formato compacto a propósito: arrays paralelos en vez de un objeto por fila, tasas como
# enteros x10.000 y edades implícitas por índice. Los tres CSV equivalentes pesan 283 KB,
# que es demasiado para hacérselo descargar a un navegador.
edades = list(range(0, 121, 3))
series = {}
for dimension, sql in [
    ('global', "dimension='global'"),
    ('plazo', "dimension='plazo'"),
    ('importe', "dimension='importe'"),
]:
    filas = tabla(f"""
        SELECT cohorte, nivel, edad, tasa_acum_pct FROM curvas
        WHERE {sql} AND edad <= 120 AND observable ORDER BY cohorte, nivel, edad
    """)
    for (cohorte, nivel), grupo in filas.groupby(['cohorte', 'nivel']):
        por_edad = dict(zip(grupo.edad, grupo.tasa_acum_pct))
        # None donde la cohorte deja de ser legible: el explorador corta la línea ahí
        # en vez de dibujar una caída falsa hasta cero.
        series.setdefault(dimension, {}).setdefault(str(nivel), {})[str(cohorte)] = [
            None if e not in por_edad else round(por_edad[e] * 10000) for e in edades
        ]

destino = TABLAS / 'explorador-anadas.json'
destino.write_text(json.dumps({
    'edades': edades,
    'escala': 10000,
    'unidad': 'cumulative charge-off rate, %',
    'series': series,
}, separators=(',', ':')), encoding='utf-8')

print(f'Figuras en {GRAFICOS.relative_to(BASE)}:')
for f in sorted(GRAFICOS.glob('*.png')):
    print(f'  {f.name:38s} {f.stat().st_size / 1024:7.1f} KB')
kb = destino.stat().st_size / 1024
print(f'\n{destino.name}: {kb:.1f} KB', '(objetivo < 100 KB)' if kb < 100 else '<-- PASA DE 100 KB')

con.close()
