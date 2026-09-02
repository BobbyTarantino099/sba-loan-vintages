"""Descarga los cuatro extractos FOIA del programa 7(a) a datos/crudos/ y registra su huella.

La SBA refresca estos archivos cada trimestre y **sobrescribe la misma URL**, así que el
`AsOfDate` del archivo que descargues hoy no será el del análisis. Los crudos no se versionan
(901 MB), de modo que este script es la única forma de reconstruirlos — y los sha256 de abajo
son la única forma de saber si reconstruiste los mismos.

Si lo ejecutas de nuevo y los hashes no coinciden con los de `documentacion/fichas-de-fuente.md`,
tienes datos más recientes que los del caso. Eso es esperado, no un error: las cifras cambiarán y
hay que rehacer la reconciliación de la fase 3 antes de dar por bueno nada.

Uso:  python notebooks/descargar.py
      python notebooks/descargar.py --solo-hashes   (no descarga; solo huella de lo que ya hay)
"""

import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CRUDOS = BASE / 'datos' / 'crudos'
DOCUMENTACION = BASE / 'documentacion'

RECURSOS = 'https://data.sba.gov/sites/default/files/uploaded_resources'

# Fecha de corte del publicador (AsOfDate), no la fecha de descarga: es lo que identifica
# el contenido. Aparece en el nombre remoto abreviada como AAMMDD.
CORTE = '2026-06-30'
CORTE_REMOTO = '260630'

# nombre remoto -> nombre local, siguiendo origen_tema_periodo_version
ARCHIVOS = {
    f'FOIA_7a_FY1991_FY1999_asof_{CORTE_REMOTO}.csv': f'sba_7a_1991-1999_{CORTE}.csv',
    f'FOIA_7a_FY2000_FY2009_asof_{CORTE_REMOTO}.csv': f'sba_7a_2000-2009_{CORTE}.csv',
    f'FOIA_7a_FY2010_FY2019_asof_{CORTE_REMOTO}.csv': f'sba_7a_2010-2019_{CORTE}.csv',
    f'FOIA_7a_FY2020_Present_asof_{CORTE_REMOTO}.csv': f'sba_7a_2020-2026_{CORTE}.csv',
}

# El diccionario oficial sí se versiona: pesa 24 KB y es lo que define `EXEMPT`, que es de
# donde cuelga todo el caso. Sin él, la decisión sobre el denominador no se puede auditar.
DICCIONARIO = ('7a_504_foia_data_dictionary.xlsx', 'sba_diccionario_oficial.xlsx')


def descargar(url, destino):
    peticion = urllib.request.Request(url, headers={'User-Agent': 'curl/8'})
    with urllib.request.urlopen(peticion) as respuesta, open(destino, 'wb') as f:
        shutil.copyfileobj(respuesta, f)


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def main():
    solo_hashes = '--solo-hashes' in sys.argv
    CRUDOS.mkdir(parents=True, exist_ok=True)
    DOCUMENTACION.mkdir(parents=True, exist_ok=True)

    tareas = [(RECURSOS + '/' + r, CRUDOS / l) for r, l in ARCHIVOS.items()]
    tareas.append((RECURSOS + '/' + DICCIONARIO[0], DOCUMENTACION / DICCIONARIO[1]))

    for url, destino in tareas:
        if not solo_hashes:
            print(f'descargando {destino.name} ...', flush=True)
            descargar(url, destino)
        elif not destino.exists():
            print(f'{destino.name}: NO EXISTE — ejecuta sin --solo-hashes')
            continue
        print(f'{destino.name}\n  {destino.stat().st_size:,} bytes\n  sha256 {sha256(destino)}')


if __name__ == '__main__':
    main()
