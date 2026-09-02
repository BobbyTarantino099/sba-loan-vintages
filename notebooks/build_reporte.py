"""Builds entregables/reporte-tecnico.html and .pdf — the case's technical report.

This is the artefact that answers "how do I know you did it properly". The executive
summary is for the client and answers "what should we do"; CASO.md has everything but is
five hundred lines of evidence. This condenses the method: the phases, the decisions that
could have gone another way, and where it ended.

Content is written HERE, not parsed from CASO.md — same rule as build_docx.py, so the two
stay in sync deliberately rather than by regex accident. Keep it to five or six pages: if
it needs more, it is turning into CASO.md and the point is lost.

The layout lives in reporte.py and is shared by every case; only the colour changes, from
the same theme the figures use. Run: python notebooks/build_reporte.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
G = BASE / 'salidas' / 'graficos'

doc = reporte.Reporte(
    titulo='<Case title: the finding, not the topic>',
    acento='#1f5fa8',   # el mismo acento que el caso pasa a estilo.aplicar()
    contra='#c2410c',
)

doc.portada(
    eyebrow='Technical report · Portfolio case study',
    hallazgo='<2-3 sentences: what was tested and what came out. Same claim as the site.>',
    meta=[
        ('Domain', '<sector>'),
        ('Tools', '<SQL · Python · …>'),
        ('Scale', '<N rows · N sources>'),
        ('Sources', '<source A · source B>'),
        ('Window', '<period analysed>'),
        ('Published', '<DD Month YYYY>'),
    ],
    figura=G / '01_<hero>.png',
    pie_figura='<What the chart shows, for someone who cannot see it.>',
)

# Una fila por fase: (etiqueta, qué se decidió, el detalle que lo justifica).
doc.seccion('The phases, and what each one settled', salto=True)
doc.fases([
    ('0 · Choose', '<what the decision sheet settled>', '<why it mattered>'),
    ('1 · Ask', '<the SMART question and the hypothesis>', '<…>'),
    ('2 · Prepare', '<sources, ROCCC, biases found>', '<…>'),
    ('3 · Process', '<tool and the reconciliation>', '<…>'),
    ('4 · Analyse', '<metrics and checks>', '<…>'),
    ('5 · Share', '<figures and their form>', '<…>'),
    ('6 · Act', '<recommendations>', '<…>'),
    ('7 · Portfolio', '<published against the contract>', '<…>'),
])
doc.cerrar()

# Seis u ocho de las del registro. La alternativa descartada es la línea que importa:
# es lo que muestra que la decisión fue razonada y no refleja.
doc.seccion('The decisions that defined the case', salto=True)
doc.decisiones([
    ('<decision>', '<why>', '<what was discarded, and why not>'),
])
doc.cerrar()

# Todo caso tiene un momento en que pudo salir mal. Ese merece su propia página.
doc.seccion('The moment the case nearly went the other way', salto=True)
doc.critico('<what it was>', ['<what would have happened if it had gone unnoticed>'])
doc.cerrar()

doc.seccion('What the data says', salto=True)
doc.figura(G / '02_<figura>.png', '<caption>')
doc.html_libre('<p>…</p>')
doc.cerrar()

doc.seccion('What each check ruled out', salto=True)
doc.tabla(['Check', 'What it ruled out'], [['V1 · …', '…']])
doc.cerrar()

doc.seccion('Conclusions, limits and what this case demonstrates', salto=True)
doc.html_libre('<h3>Recommendations</h3><ul><li>…</li></ul>')
doc.pie('Full phase log and cleaning log: <strong>CASO.md</strong> in the case repository.')
doc.cerrar()

doc.escribir(BASE / 'entregables' / 'reporte-tecnico.html')
