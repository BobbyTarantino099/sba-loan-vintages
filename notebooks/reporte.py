"""Motor del reporte técnico del caso: HTML autocontenido que se imprime a PDF.

Existe porque ninguno de los otros entregables cuenta *cómo se llegó* al resultado. El
resumen ejecutivo es de negocio; `CASO.md` tiene las fases y las decisiones pero son
quinientas líneas de Markdown, que es evidencia y no un documento que se lea del tirón.
Este reporte condensa el método: las ocho fases, las decisiones que podían haber ido de
otra forma, y en qué acabó.

Sigue el patrón de `site/docs/arquitectura.html`: una sola pieza de HTML, sin recursos
externos, con `@page` y `@media print`. Las figuras van embebidas en base64, así que el
archivo se puede mandar por correo tal cual y sigue funcionando.

Uso, desde el `build_reporte.py` de cada caso:

    import reporte
    doc = reporte.Reporte(titulo=..., acento='#0f7d3f')
    doc.portada(...)
    doc.fases([...])
    doc.decisiones([...])
    doc.escribir(RUTA_BASE / 'entregables' / 'reporte-tecnico.html')

**El contenido se escribe a mano en cada caso, no se parsea del Markdown.** Es el mismo
criterio que `build_docx.py`: que los dos textos se mantengan sincronizados a propósito
y no por accidente de una expresión regular.

Lo que cambia por caso es el color; la maqueta no. Igual que en `estilo.py`, y por la
misma razón: es lo que hace que dos reportes parezcan del mismo autor.
"""

import base64
import html
import os
import shutil
import subprocess
from pathlib import Path

# El PDF se genera con `--headless --print-to-pdf`, para que el binario salga de un script
# y no de imprimirlo a mano desde el navegador.
#
# Las ubicaciones se construyen desde variables de entorno en vez de escribirse enteras:
# una ruta absoluta incrustada convierte un script reproducible en uno que solo corría en
# la máquina donde se escribió. Si nada de esto existe, se busca en el PATH, y si tampoco,
# el HTML se genera igual y el PDF se obtiene imprimiéndolo.
_SUFIJOS = [
    ('Google', 'Chrome', 'Application', 'chrome.exe'),
    ('Microsoft', 'Edge', 'Application', 'msedge.exe'),
]
_RAICES = ('ProgramFiles', 'ProgramFiles(x86)', 'LOCALAPPDATA')
_EN_PATH = ('google-chrome', 'chromium', 'chromium-browser', 'chrome')


def _navegador():
    for var in _RAICES:
        raiz = os.environ.get(var)
        if not raiz:
            continue
        for sufijo in _SUFIJOS:
            ruta = Path(raiz).joinpath(*sufijo)
            if ruta.exists():
                return ruta
    for nombre in _EN_PATH:
        encontrado = shutil.which(nombre)
        if encontrado:
            return Path(encontrado)
    return None


def _img_base64(ruta):
    datos = base64.b64encode(Path(ruta).read_bytes()).decode('ascii')
    return f'data:image/png;base64,{datos}'


def _e(texto):
    """Escapa para HTML. El contenido lo escribe una persona, pero un `&` suelto en el
    nombre de un club rompería el documento en silencio."""
    return html.escape(str(texto))


_CSS = """
:root {
  --acento: %(acento)s;
  --acento-suave: %(acento_suave)s;
  --contra: %(contra)s;
  --tinta: #1a1815;
  --tinta-suave: #4a463f;
  --tinta-tenue: #7d7970;
  --regla: #e2e0d9;
  --fondo-sutil: #faf9f6;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 0 0 4rem;
  font-family: ui-sans-serif, system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: var(--tinta);
  background: #fff;
  -webkit-font-smoothing: antialiased;
}

.hoja { max-width: 190mm; margin: 0 auto; padding: 0 4mm; }

h1, h2, h3 { line-height: 1.2; margin: 0; }
h1 { font-size: 24pt; letter-spacing: -0.015em; }
h2 {
  font-size: 14pt;
  margin: 2.2rem 0 0.9rem;
  padding-bottom: 0.35rem;
  border-bottom: 2px solid var(--acento);
}
h3 { font-size: 11pt; margin: 1.2rem 0 0.35rem; }
p { margin: 0 0 0.7rem; }
strong { font-weight: 640; }
em { color: var(--tinta-suave); }

.eyebrow {
  font-size: 8pt;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--acento);
  font-weight: 650;
  margin-bottom: 0.5rem;
}

/* --- Portada -------------------------------------------------------------- */

.portada { padding-top: 2rem; }
.portada .hallazgo {
  font-size: 12.5pt;
  color: var(--tinta-suave);
  margin: 0.9rem 0 1.4rem;
  max-width: 62ch;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0 2.2rem;
  padding: 0.8rem 0;
  border-top: 1px solid var(--regla);
  border-bottom: 1px solid var(--regla);
  margin-bottom: 1.4rem;
}
.meta div { padding: 0.15rem 0; }
.meta dt {
  font-size: 7.5pt;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--tinta-tenue);
  font-weight: 650;
}
.meta dd { margin: 0.1rem 0 0; font-size: 9.5pt; }

/* --- Figuras -------------------------------------------------------------- */

figure {
  margin: 1rem 0 1.2rem;
  padding: 0.5rem;
  background: #fff;
  border: 1px solid var(--regla);
  border-radius: 4px;
  page-break-inside: avoid;
}
figure img { width: 100%%; height: auto; display: block; }
figcaption {
  font-size: 8.5pt;
  color: var(--tinta-tenue);
  padding: 0.5rem 0.3rem 0.15rem;
}

/* --- Línea de tiempo de fases --------------------------------------------- */

.fases { margin: 0.6rem 0 0; }
.fase {
  display: grid;
  grid-template-columns: 4.6rem 1fr;
  gap: 0 0.9rem;
  padding: 0.55rem 0;
  border-top: 1px solid var(--regla);
  page-break-inside: avoid;
}
.fase:first-child { border-top: 0; }
.fase .n {
  font-size: 8pt;
  font-weight: 650;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--acento);
  padding-top: 0.12rem;
}
.fase .q { font-weight: 640; }
.fase .d { color: var(--tinta-suave); }

/* --- Tarjetas de decisión ------------------------------------------------- */

.decision {
  border-left: 3px solid var(--acento);
  background: var(--fondo-sutil);
  padding: 0.7rem 0.9rem;
  margin: 0 0 0.7rem;
  page-break-inside: avoid;
}
.decision .que { font-weight: 640; margin-bottom: 0.25rem; }
.decision .por { color: var(--tinta-suave); margin-bottom: 0.3rem; }
.decision .alt {
  font-size: 9pt;
  color: var(--tinta-tenue);
  padding-top: 0.3rem;
  border-top: 1px dashed var(--regla);
}
.decision .alt b { color: var(--contra); font-weight: 650; }

/* --- Bloque destacado ----------------------------------------------------- */

.critico {
  border: 1px solid var(--acento);
  border-radius: 4px;
  padding: 0.9rem 1rem;
  margin: 0.8rem 0 1rem;
  page-break-inside: avoid;
}
.critico .titulo {
  color: var(--acento);
  font-weight: 650;
  margin-bottom: 0.4rem;
}

/* --- Tablas --------------------------------------------------------------- */

table {
  width: 100%%;
  border-collapse: collapse;
  font-size: 9pt;
  margin: 0.7rem 0 1rem;
  page-break-inside: avoid;
}
th {
  text-align: left;
  font-size: 7.5pt;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--tinta-tenue);
  border-bottom: 1.5px solid var(--tinta-suave);
  padding: 0.3rem 0.5rem 0.3rem 0;
}
td {
  padding: 0.32rem 0.5rem 0.32rem 0;
  border-bottom: 1px solid var(--regla);
  vertical-align: top;
}
tbody tr:nth-child(even) td { background: var(--fondo-sutil); }
td.num { font-variant-numeric: tabular-nums; white-space: nowrap; }

ul { margin: 0 0 0.7rem; padding-left: 1.1rem; }
li { margin-bottom: 0.22rem; }
li::marker { color: var(--acento); }

.pie {
  margin-top: 2rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--regla);
  font-size: 8.5pt;
  color: var(--tinta-tenue);
}

/* --- Impresión ------------------------------------------------------------ */

@page { size: A4; margin: 14mm 12mm; }

@media print {
  body { padding: 0; font-size: 9.8pt; }
  .hoja { max-width: none; padding: 0; }
  .salto { page-break-before: always; }
  h2 { page-break-after: avoid; }
  a { color: inherit; text-decoration: none; }
}
"""


class Reporte:
    """Acumula secciones y las ensambla en un HTML de una sola pieza."""

    def __init__(self, titulo, acento='#1f5fa8', contra='#c2410c', acento_suave=None):
        self.titulo = titulo
        self.acento = acento
        self.contra = contra
        self.acento_suave = acento_suave or acento
        self._partes = []

    # -- piezas ------------------------------------------------------------

    def portada(self, eyebrow, hallazgo, meta, figura=None, pie_figura=None):
        campos = ''.join(
            f'<div><dt>{_e(k)}</dt><dd>{_e(v)}</dd></div>' for k, v in meta
        )
        fig = ''
        if figura:
            fig = (f'<figure><img src="{_img_base64(figura)}" alt="">'
                   + (f'<figcaption>{_e(pie_figura)}</figcaption>' if pie_figura else '')
                   + '</figure>')
        self._partes.append(f"""
<section class="portada">
  <p class="eyebrow">{_e(eyebrow)}</p>
  <h1>{_e(self.titulo)}</h1>
  <p class="hallazgo">{_e(hallazgo)}</p>
  <dl class="meta">{campos}</dl>
  {fig}
</section>""")
        return self

    def seccion(self, titulo, intro=None, salto=False):
        clase = ' class="salto"' if salto else ''
        cuerpo = f'<p>{intro}</p>' if intro else ''
        self._partes.append(f'<section{clase}><h2>{_e(titulo)}</h2>{cuerpo}')
        return self

    def cerrar(self):
        self._partes.append('</section>')
        return self

    def fases(self, filas):
        """filas: (etiqueta, qué se decidió, detalle)."""
        items = ''.join(
            f'<div class="fase"><div class="n">{_e(n)}</div>'
            f'<div><div class="q">{_e(q)}</div><div class="d">{_e(d)}</div></div></div>'
            for n, q, d in filas
        )
        self._partes.append(f'<div class="fases">{items}</div>')
        return self

    def decisiones(self, filas):
        """filas: (decisión, motivo, alternativa descartada)."""
        for que, por, alt in filas:
            self._partes.append(
                f'<div class="decision"><div class="que">{_e(que)}</div>'
                f'<div class="por">{_e(por)}</div>'
                f'<div class="alt"><b>Discarded:</b> {_e(alt)}</div></div>'
            )
        return self

    def critico(self, titulo, parrafos):
        cuerpo = ''.join(f'<p>{p}</p>' for p in parrafos)
        self._partes.append(
            f'<div class="critico"><div class="titulo">{_e(titulo)}</div>{cuerpo}</div>'
        )
        return self

    def tabla(self, cabeceras, filas, numericas=()):
        th = ''.join(f'<th>{_e(c)}</th>' for c in cabeceras)
        cuerpo = ''
        for fila in filas:
            tds = ''.join(
                f'<td class="num">{_e(v)}</td>' if i in numericas else f'<td>{_e(v)}</td>'
                for i, v in enumerate(fila)
            )
            cuerpo += f'<tr>{tds}</tr>'
        self._partes.append(
            f'<table><thead><tr>{th}</tr></thead><tbody>{cuerpo}</tbody></table>'
        )
        return self

    def figura(self, ruta, pie=None):
        self._partes.append(
            f'<figure><img src="{_img_base64(ruta)}" alt="">'
            + (f'<figcaption>{_e(pie)}</figcaption>' if pie else '')
            + '</figure>'
        )
        return self

    def html_libre(self, fragmento):
        """Para prosa con énfasis. El contenido lo escribe una persona, así que aquí
        no se escapa: es la vía de escape deliberada del motor."""
        self._partes.append(fragmento)
        return self

    def pie(self, texto):
        self._partes.append(f'<p class="pie">{texto}</p>')
        return self

    # -- salida ------------------------------------------------------------

    def render(self):
        css = _CSS % {
            'acento': self.acento,
            'acento_suave': self.acento_suave,
            'contra': self.contra,
        }
        return (
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{_e(self.titulo)}</title>\n<style>{css}</style>\n</head>\n'
            f'<body>\n<main class="hoja">\n{"".join(self._partes)}\n</main>\n</body>\n</html>\n'
        )

    def escribir(self, destino, pdf=True):
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(self.render(), encoding='utf-8')
        print(f'{destino.name:<28} {destino.stat().st_size / 1024:>7.0f} KB')

        if not pdf:
            return destino
        navegador = _navegador()
        if navegador is None:
            print('  (sin Chrome: el PDF se obtiene abriendo el HTML e imprimiendo)')
            return destino

        salida_pdf = destino.with_suffix('.pdf')
        subprocess.run(
            [str(navegador), '--headless', '--disable-gpu', '--no-pdf-header-footer',
             f'--print-to-pdf={salida_pdf}', destino.resolve().as_uri()],
            check=True, capture_output=True, timeout=180,
        )
        print(f'{salida_pdf.name:<28} {salida_pdf.stat().st_size / 1024:>7.0f} KB')
        return salida_pdf
