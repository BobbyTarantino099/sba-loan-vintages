"""
Identidad visual de las figuras del portafolio.

Copiar este archivo (y la carpeta `fuentes/`) a `notebooks/` del caso y usarlo así:

    import estilo
    estilo.aplicar()

    fig, ax = estilo.figura(
        titular="EL HALLAZGO en una frase, no el tema",
        subtitulo="La metrica exacta que se esta midiendo",
        periodo="Alcance de los datos, con su periodo",
        fuente="Fuente y licencia",
    )
    ...  # dibujar sobre ax
    estilo.guardar(fig, "salidas/graficos/01_ejemplo.png")

Ya viene en la plantilla: no se copia a mano por caso ni se edita por caso. Si una
figura necesita algo que no esta aqui, se anade a este archivo en la plantilla y
baja a los casos siguientes — asi el catalogo de formas crece para todos.

**Lo que si cambia por caso es el color.** `aplicar()` acepta acento, contraste y
rampa, de modo que cada caso declara su tema en una linea y hereda todo lo demas:

    estilo.aplicar(acento="#0f7d3f", contra="#7b4bb0", rampa=[...])

La frontera esta puesta a proposito. El color distingue un caso de otro y demuestra
que la visualizacion se adapta al asunto; la composicion —cabecera de tres niveles,
tipografia, ritmo vertical, nota de fuente, firma— no se toca, porque es lo que hace
que seis casos parezcan un cuerpo de trabajo y no seis encargos sueltos. Cambia el
color y sigue siendo tuyo; cambia la maqueta y parece de otra persona.

Por qué existe: el anexo de visualización pedía "un color protagonista" sin decir
cuál, y cada caso reinventaba la composición. El resultado eran figuras correctas
en principio y genéricas en la práctica. Aquí la identidad está en el código, así
que sale bien por defecto en vez de depender de recordar doce reglas.

La paleta está validada con el verificador de la skill `dataviz`: banda de
luminosidad, suelo de croma, separación para daltonismo (ΔE 21.9 protan, 30.8
tritan), suelo de visión normal (ΔE 30.0) y contraste sobre el fondo. La rampa
secuencial es monótona y cada escalón sabe si su texto va en tinta o en blanco.
"""

from pathlib import Path
import textwrap

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------

#: Azul protagonista. Es el mismo acento del sitio: figura y página hablan igual.
ACENTO = "#1f5fa8"

#: Cálido secundario, para el otro lado de una comparación de dos estados.
CONTRA = "#c2410c"

#: Gris de contexto. 3.6:1 sobre blanco — por encima del 3:1 que piden los
#: elementos gráficos con significado.
CONTEXTO = "#8a877c"

TINTA = "#1a1815"       # titulares y cifras
TINTA_SUAVE = "#5a564c"  # subtítulos y etiquetas
TINTA_TENUE = "#807d73"  # notas de fuente y periodo
REGLA = "#e2e0d9"        # separadores
PAPEL = "#ffffff"        # el sitio muestra las figuras sobre blanco fijo

#: Rampa secuencial de un solo tono, clara → oscura. Luminancia monótona.
RAMPA = ["#eaf1f9", "#c7dcf0", "#8fbce2", "#4a8bc9", "#1f5fa8"]

#: A partir de este índice de la rampa el texto encima va en blanco.
_RAMPA_TEXTO_BLANCO = 4

FIRMA = "JEA"

# ---------------------------------------------------------------------------
# Ritmo vertical de la cabecera
# ---------------------------------------------------------------------------
#
# En PUNTOS, no en fracción del lienzo. Es la diferencia entre un diseño y una
# coincidencia: la tipografía se mide en puntos, así que si el aire se expresa
# como fracción de la altura de la figura, el mismo diseño se aprieta al bajar
# el lienzo y se desparrama al subirlo. Con una figura de 6.2" de alto el aire
# entre titular y subtítulo llegaba a cero y los dos se solapaban.
#
# Tocar estos cuatro números cambia el espaciado de todas las figuras a la vez,
# que es justo lo que hace que se vean como una familia.

TAM_TITULAR = 19.0
TAM_SUBTITULO = 11.5
TAM_PERIODO = 8.5

GAP_TITULAR_SUB = 14.0    # pt entre el titular y el subtítulo
GAP_SUB_PERIODO = 9.0     # pt entre el subtítulo y la línea de periodo
GAP_CABECERA_EJE = 26.0   # pt entre la cabecera y el borde superior de los ejes

# ---------------------------------------------------------------------------
# Tipografía
# ---------------------------------------------------------------------------

_DIR = Path(__file__).resolve().parent
_FUENTES = _DIR / "fuentes"

# Cada peso se referencia por archivo. Resolver por familia + `fontweight` es
# frágil: depende de metadatos internos del TTF y falla en silencio cayendo al
# tipo por defecto.
_ARCHIVOS = {
    "regular": _FUENTES / "Inter-Regular.ttf",
    "medio": _FUENTES / "Inter-SemiBold.ttf",
    "negrita": _FUENTES / "Inter-Bold.ttf",
}

_PROPS: dict[str, fm.FontProperties | None] = {}


def _prop(peso: str, tam: float) -> dict:
    """Devuelve kwargs de fuente para un peso y tamaño.

    Si Inter no está disponible, devuelve solo el tamaño y matplotlib usa su
    tipografía por defecto: la figura sale, más fea pero sin romperse.
    """
    base = _PROPS.get(peso)
    if base is None:
        return {"fontsize": tam}
    p = base.copy()
    p.set_size(tam)
    return {"fontproperties": p}


def aplicar(acento=None, contra=None, rampa=None) -> None:
    """Registra la tipografía y fija los rcParams de la identidad.

    Los tres argumentos opcionales son el **tema del caso**. Sin ellos queda el
    tema por defecto, así que un caso que no declare nada sigue saliendo igual.

    Lo que un caso puede cambiar es el color; lo que no, la composición. La
    cabecera de tres niveles, la tipografía, el ritmo vertical y la firma son lo
    que hace reconocible el trabajo entre casos: con otro color sigue siendo del
    mismo autor, con otra maqueta parece de otro. Un caso que necesite algo que
    no está aquí lo añade a ESTE archivo en la plantilla, no a su copia.

        estilo.aplicar(acento='#0f7d3f', contra='#7b4bb0', rampa=[...])

    Toda paleta nueva se valida antes con el verificador de la skill `dataviz`
    (banda de luminosidad, suelo de croma, separación para daltonismo, contraste)
    y las rampas, además, por monotonicidad de luminancia. No se eligen a ojo.
    """
    global ACENTO, CONTRA, RAMPA
    if acento:
        ACENTO = acento
    if contra:
        CONTRA = contra
    if rampa:
        RAMPA = list(rampa)

    for peso, ruta in _ARCHIVOS.items():
        if ruta.exists():
            fm.fontManager.addfont(str(ruta))
            _PROPS[peso] = fm.FontProperties(fname=str(ruta))
        else:
            _PROPS[peso] = None

    matplotlib.rcParams.update({
        "figure.facecolor": PAPEL,
        "axes.facecolor": PAPEL,
        "savefig.facecolor": PAPEL,
        # Chrome mínimo: sin marco superior ni derecho.
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.edgecolor": REGLA,
        "axes.linewidth": 0.9,
        "axes.labelcolor": TINTA_SUAVE,
        "axes.titlesize": 11,
        "text.color": TINTA,
        "xtick.color": TINTA_TENUE,
        "ytick.color": TINTA_SUAVE,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 10,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "grid.color": "#f0eee8",
        "grid.linewidth": 0.9,
        "legend.frameon": False,
        "figure.dpi": 110,
    })
    if _PROPS.get("regular") is not None:
        matplotlib.rcParams["font.family"] = "Inter"


# ---------------------------------------------------------------------------
# Composición
# ---------------------------------------------------------------------------

def figura(titular, subtitulo=None, periodo=None, fuente=None, nota=None,
           figsize=(9.0, 6.6), izquierda=0.085, derecha=0.975, abajo=0.16):
    """Crea la figura con el bloque de cabecera, la fuente y la firma ya puestos.

    El bloque de cabecera es lo que da identidad: titular pesado, subtítulo gris
    que define la métrica, y una tercera línea opcional en versalitas con el
    alcance. El salto de tamaño y color entre los tres niveles es deliberado.

    El aire entre niveles sale de las constantes `GAP_*`, en puntos, y el alto
    de cada nivel se mide del texto ya dibujado. Así el espaciado es el mismo en
    pulgadas sea cual sea el tamaño del lienzo.

    `abajo` no baja de 0.16: por debajo de eso el rótulo del eje X se solapa con
    la nota de fuente cuando la nota ocupa dos líneas.
    """
    fig = plt.figure(figsize=figsize)
    ancho_util = derecha - izquierda

    # Ancho de envoltura estimado a partir del ancho real en pulgadas.
    pulgadas = figsize[0] * ancho_util

    def gap(puntos):
        """Puntos -> fracción de la altura de la figura."""
        return puntos / (figsize[1] * 72.0)

    def poner(texto, y, tam, peso, color, interlineado, ancho):
        """Dibuja un nivel de la cabecera y devuelve la `y` del siguiente.

        Mide el alto real del texto ya compuesto en vez de estimarlo a partir
        del número de caracteres: `textwrap` ya sabe cuántas líneas salieron, y
        el renderizador sabe cuánto ocupan.
        """
        t = fig.text(izquierda, y, "\n".join(textwrap.wrap(texto, width=ancho)),
                     va="top", ha="left", color=color, linespacing=interlineado,
                     **_prop(peso, tam))
        caja = t.get_window_extent(renderer=fig.canvas.get_renderer())
        return y - caja.transformed(fig.transFigure.inverted()).height

    y = 0.965
    y = poner(titular, y, TAM_TITULAR, "negrita", TINTA, 1.22, int(pulgadas * 6.4))

    if subtitulo:
        y -= gap(GAP_TITULAR_SUB)
        y = poner(subtitulo, y, TAM_SUBTITULO, "regular", TINTA_SUAVE, 1.3,
                  int(pulgadas * 11))

    if periodo:
        y -= gap(GAP_SUB_PERIODO)
        y = poner(periodo.upper(), y, TAM_PERIODO, "medio", TINTA_TENUE, 1.2,
                  int(pulgadas * 15))

    arriba = max(y - gap(GAP_CABECERA_EJE), 0.45)
    ax = fig.add_axes([izquierda, abajo, ancho_util, arriba - abajo])

    pie = []
    if fuente:
        pie.append(f"Source: {fuente}")
    if nota:
        pie.append(nota)
    if pie:
        # Anclado por abajo, no por arriba: con `va="top"` una nota de dos
        # líneas crece hacia fuera del lienzo y se corta al guardar.
        fig.text(izquierda, 0.022, "\n".join(
            textwrap.wrap("  ·  ".join(pie), width=int(pulgadas * 16))),
            va="bottom", ha="left", color=TINTA_TENUE, linespacing=1.35,
            **_prop("regular", 7.8))

    # Firma. Texto, no imagen: no arrastra un archivo por caso.
    fig.text(derecha, 0.022, FIRMA, va="bottom", ha="right", color=TINTA_TENUE,
             **_prop("negrita", 9))

    return fig, ax


def guardar(fig, ruta, dpi=200) -> None:
    """Guarda con dpi y fondo uniformes. Sin `bbox_inches='tight'`: recortaría
    el bloque de cabecera y la firma, que viven fuera de los ejes."""
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=dpi, facecolor=PAPEL)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Ayudas de dibujo
# ---------------------------------------------------------------------------

def destacar(categorias, protagonistas, acento=None, resto=None):
    """Contraste dirigido: acento para las protagonistas, gris para el resto.

    Los colores se resuelven aquí y no en la firma: un default evaluado al
    importar el módulo congelaría el color antes de que el caso declare su tema.
    """
    acento = acento or ACENTO
    resto = resto or CONTEXTO
    p = set(protagonistas)
    return [acento if c in p else resto for c in categorias]


def leyenda(ax, tam=9, holgura_max=0.45, **kwargs):
    """Leyenda en el hueco más libre de datos, enmarcada como un bloque.

    Dos decisiones, y son independientes:

    **Dónde.** `loc="best"` — matplotlib ya evalúa el solapamiento con líneas,
    parches y colecciones y elige el ancla con menos. Fijarla a mano
    (`"lower right"`) funciona hasta que los datos cambian de forma: así fue
    como una leyenda acabó metida entre las barras del primer grupo.

    **Cómo.** Relleno opaco y borde fino. El relleno importa tanto como el
    borde: es lo que la despega de la cuadrícula y la convierte en un bloque en
    vez de texto flotando encima del gráfico.

    Y una red de seguridad: si ni el mejor sitio está libre —barras desde cero
    que llenan el panel, por ejemplo— `best` devuelve "la esquina menos mala" y
    el problema sigue ahí. En ese caso se sube el techo del eje hasta abrirle
    sitio de verdad. La base en cero no se toca, así que no distorsiona nada:
    solo añade aire arriba.
    """
    fig = ax.figure
    y0, y1 = ax.get_ylim()

    def dibujar():
        leg = ax.legend(loc="best", frameon=True, fancybox=False, framealpha=1.0,
                        facecolor=PAPEL, edgecolor=REGLA, borderpad=0.7,
                        labelspacing=0.55, handletextpad=0.6, **kwargs)
        leg.get_frame().set_linewidth(0.9)
        for t in leg.get_texts():
            t.set_color(TINTA_SUAVE)
            t.set_fontsize(tam)
        return leg

    leg = dibujar()
    if not _pisa_datos(ax, leg):
        return leg

    # Ampliar el eje sin más no basta: `best` ya eligió y no se reevalúa solo.
    # Hay que abrir el hueco y volver a colocarla, en el mínimo paso que sirva.
    for paso in (0.12, 0.22, 0.34, holgura_max):
        ax.set_ylim(y0, y0 + (y1 - y0) * (1 + paso))
        leg.remove()
        fig.canvas.draw()
        leg = dibujar()
        if not _pisa_datos(ax, leg):
            return leg
    return leg


def _pisa_datos(ax, leg) -> bool:
    """¿La leyenda se superpone a alguna marca dibujada?"""
    r = ax.figure.canvas.get_renderer()
    caja = leg.get_window_extent(renderer=r)
    for art in list(ax.patches) + list(ax.lines) + list(ax.collections):
        try:
            otra = art.get_window_extent(renderer=r)
        except (AttributeError, ValueError, TypeError):
            continue
        if otra.width <= 0 or otra.height <= 0:
            continue
        if caja.overlaps(otra):
            return True
    return False


def anotar(ax, texto, xy, xytexto, color=TINTA_SUAVE, tam=9, flecha=True):
    """Anotación directiva, con el estilo de las referencias: texto corto que
    señala un punto concreto en vez de un párrafo debajo del gráfico."""
    ax.annotate(
        texto, xy=xy, xytext=xytexto, color=color,
        arrowprops=dict(arrowstyle="-", color=REGLA, linewidth=1.1,
                        shrinkA=2, shrinkB=4) if flecha else None,
        **_prop("regular", tam),
    )


def dumbbell(ax, categorias, desde, hasta, etiqueta_desde=None, etiqueta_hasta=None,
             color_desde=None, color_hasta=None, destacadas=None):
    """Dumbbell: dos estados por categoría, unidos por una barra.

    Es la forma correcta cuando la pregunta es "cuánto cambia de A a B por
    categoría". Unas barras agrupadas obligan a comparar dos longitudes desde
    ejes distintos; el dumbbell muestra la diferencia como una distancia.

    Cuidado con `destacadas`: atenúa las filas no elegidas hasta dejar sus dos
    extremos en gris, y entonces deja de verse cuál es cuál. Úsalo solo cuando
    la comparación de esas filas de verdad no importe.
    """
    color_desde = color_desde or CONTEXTO
    color_hasta = color_hasta or ACENTO
    y = range(len(categorias))
    destacadas = set(destacadas or [])
    for i, (c, a, b) in enumerate(zip(categorias, desde, hasta)):
        fuerte = not destacadas or c in destacadas
        ax.plot([a, b], [i, i], color=color_hasta if fuerte else REGLA,
                linewidth=3.2 if fuerte else 2.4, solid_capstyle="round",
                alpha=1.0 if fuerte else 0.55, zorder=1)
        ax.scatter([a], [i], s=62, color=color_desde, zorder=2,
                   edgecolor=PAPEL, linewidth=1.6)
        ax.scatter([b], [i], s=72, color=color_hasta if fuerte else CONTEXTO,
                   zorder=3, edgecolor=PAPEL, linewidth=1.6)

    ax.set_yticks(list(y))
    ax.set_yticklabels(categorias)
    ax.invert_yaxis()
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    # Solo registra las marcas de la clave. Quién dibuja la leyenda es
    # `leyenda()`, para que haya una sola forma de colocarla.
    if etiqueta_desde and etiqueta_hasta:
        ax.scatter([], [], s=62, color=color_desde, label=etiqueta_desde)
        ax.scatter([], [], s=72, color=color_hasta, label=etiqueta_hasta)


def slope(ax, categorias, izquierda, derecha, etiqueta_izq, etiqueta_der,
          colores=None, formato="{:.2f}"):
    """Slope: dos momentos por serie, con etiqueta directa en cada extremo.

    Se usa cuando importa la posición en cada momento y el sentido del cambio,
    no la trayectoria intermedia. Frente a una línea de muchos puntos, elimina
    el ruido de lo que pasó en medio; frente a un dumbbell, conserva el nivel
    de ambos extremos en un eje vertical legible.

    Sin leyenda a propósito: cada serie lleva su nombre escrito al lado, que es
    un salto de vista menos.
    """
    colores = colores or [ACENTO, CONTRA, CONTEXTO]
    for i, (cat, a, b) in enumerate(zip(categorias, izquierda, derecha)):
        color = colores[i % len(colores)]
        ax.plot([0, 1], [a, b], color=color, linewidth=2.6, zorder=2)
        ax.scatter([0, 1], [a, b], s=70, color=color, zorder=3,
                   edgecolor=PAPEL, linewidth=1.6)
        ax.text(-0.045, a, f"{formato.format(a)}  {cat}", va="center", ha="right",
                color=color, **_prop("medio", 10))
        ax.text(1.045, b, formato.format(b), va="center", ha="left",
                color=color, **_prop("medio", 10))

    ax.set_xlim(-0.62, 1.28)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([etiqueta_izq, etiqueta_der])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", left=False)


def barras_divergentes(ax, categorias, valores, color_positivo=None,
                       color_negativo=None, formato="{:+.0f}"):
    """Barras horizontales centradas en cero: desviación respecto de una referencia.

    Cuando el hallazgo *es* la diferencia contra un valor esperado, dibujar las
    dos series por separado obliga al lector a restar de cabeza. Aquí la resta
    ya está hecha y el cero es el eje.
    """
    color_positivo = color_positivo or ACENTO
    color_negativo = color_negativo or CONTRA
    y = range(len(categorias))
    colores = [color_positivo if v >= 0 else color_negativo for v in valores]

    ax.barh(list(y), valores, height=0.52, color=colores, zorder=2)
    ax.axvline(0, color=TINTA_SUAVE, linewidth=1.1, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(categorias)
    ax.invert_yaxis()
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    tope = max(abs(v) for v in valores)
    holgura = tope * 0.04
    for i, v in enumerate(valores):
        ax.text(v + (holgura if v >= 0 else -holgura), i, formato.format(v),
                va="center", ha="left" if v >= 0 else "right",
                color=TINTA, **_prop("medio", 9.5))

    # Sitio para las cifras a ambos lados: sin este margen la etiqueta de la barra
    # más larga se sale del eje y se monta sobre el rótulo de la categoría.
    ax.set_xlim(-tope * 1.22, tope * 1.22)


def _color_celda(valor, vmin, vmax):
    """Escalón de la rampa para un valor, y si el texto encima va en blanco."""
    if vmax == vmin:
        idx = len(RAMPA) // 2
    else:
        t = (valor - vmin) / (vmax - vmin)
        idx = min(int(t * len(RAMPA)), len(RAMPA) - 1)
    return RAMPA[idx], idx >= _RAMPA_TEXTO_BLANCO


def tabla_matriz(ax, filas, columnas, valores, formato="{:.1f}",
                 etiqueta_filas=None, vmin=None, vmax=None):
    """Tabla-figura: matriz con cada celda codificada en color y su número visible.

    Un mapa de calor obliga a leer el color y adivinar el número. Aquí el número
    manda y el color acompaña — que es lo que hacen las tablas de Sportradar.
    """
    planos = [v for fila in valores for v in fila if v is not None]
    vmin = min(planos) if vmin is None else vmin
    vmax = max(planos) if vmax is None else vmax

    n_f, n_c = len(filas), len(columnas)
    ax.set_xlim(0, n_c)
    ax.set_ylim(0, n_f)
    ax.axis("off")

    for j, col in enumerate(columnas):
        ax.text(j + 0.5, n_f + 0.22, col.upper(), ha="center", va="bottom",
                color=TINTA_SUAVE, **_prop("medio", 8.5))
    ax.plot([0, n_c], [n_f + 0.12, n_f + 0.12], color=TINTA_SUAVE,
            linewidth=1.0, clip_on=False)

    for i, fila in enumerate(filas):
        y = n_f - i - 1
        ax.text(-0.16, y + 0.5, fila, ha="right", va="center", color=TINTA,
                **_prop("medio", 10.5))
        if etiqueta_filas:
            ax.text(-0.16, y + 0.18, etiqueta_filas[i].upper(), ha="right",
                    va="center", color=TINTA_TENUE, **_prop("regular", 7.5))

        for j in range(n_c):
            v = valores[i][j]
            if v is None:
                continue
            color, texto_blanco = _color_celda(v, vmin, vmax)
            ax.add_patch(Rectangle((j + 0.035, y + 0.06), 0.93, 0.88,
                                   facecolor=color, edgecolor=PAPEL,
                                   linewidth=1.4, zorder=1))
            ax.text(j + 0.5, y + 0.5, formato.format(v), ha="center", va="center",
                    color=PAPEL if texto_blanco else TINTA, zorder=2,
                    **_prop("medio", 10.5))


def tabla_ranking(ax, entidades, valores, secundarias=None, columnas_extra=None,
                  encabezados=None, formato="{:.1f}"):
    """Ranking con la columna clave codificada — el patrón de Sportradar.

    `entidades` es la etiqueta principal; `secundarias` la línea gris de debajo;
    `columnas_extra` son columnas numéricas sin codificar; `valores` es la
    columna que lleva el color.
    """
    n = len(entidades)
    extra = columnas_extra or []
    n_extra = len(extra)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, n)
    ax.axis("off")

    x_valor, x_extra0 = 9.3, 6.6
    paso = (x_valor - x_extra0 - 0.9) / max(n_extra, 1)

    if encabezados:
        ax.text(0, n + 0.25, encabezados[0].upper(), ha="left", va="bottom",
                color=TINTA_SUAVE, **_prop("medio", 8.5))
        for k in range(n_extra):
            ax.text(x_extra0 + k * paso, n + 0.25, encabezados[1 + k].upper(),
                    ha="center", va="bottom", color=TINTA_SUAVE, **_prop("medio", 8.5))
        ax.text(x_valor, n + 0.25, encabezados[-1].upper(), ha="center",
                va="bottom", color=TINTA_SUAVE, **_prop("medio", 8.5))
    ax.plot([0, 10], [n + 0.12, n + 0.12], color=TINTA_SUAVE, linewidth=1.0, clip_on=False)

    vmin, vmax = min(valores), max(valores)
    for i in range(n):
        y = n - i - 1
        if i % 2 == 1:
            ax.add_patch(Rectangle((0, y), 10, 1, facecolor="#faf9f6",
                                   edgecolor="none", zorder=0))
        ax.text(0, y + (0.58 if secundarias else 0.5), entidades[i], ha="left",
                va="center", color=TINTA, zorder=2, **_prop("medio", 11))
        if secundarias:
            ax.text(0, y + 0.28, secundarias[i].upper(), ha="left", va="center",
                    color=TINTA_TENUE, zorder=2, **_prop("regular", 7.8))
        for k, col in enumerate(extra):
            ax.text(x_extra0 + k * paso, y + 0.5, str(col[i]), ha="center",
                    va="center", color=TINTA_SUAVE, zorder=2, **_prop("regular", 10))

        color, texto_blanco = _color_celda(valores[i], vmin, vmax)
        ax.add_patch(Rectangle((x_valor - 0.62, y + 0.14), 1.24, 0.72,
                               facecolor=color, edgecolor=PAPEL, linewidth=1.2,
                               zorder=1))
        ax.text(x_valor, y + 0.5, formato.format(valores[i]), ha="center",
                va="center", color=PAPEL if texto_blanco else TINTA, zorder=2,
                **_prop("medio", 11))
