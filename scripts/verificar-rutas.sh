#!/usr/bin/env bash
# Busca rutas absolutas antes de hacer publico el repositorio.
#
# Por que existe: el caso 1 llego a la fase 6 con rutas del sandbox donde se
# genero, y ningun script podia correr en otra maquina. No se nota hasta que
# alguien clona el repositorio para comprobar tu trabajo.
#
# Uso:   bash scripts/verificar-rutas.sh [directorio]
# Sale con 1 si encuentra algo, para poder encadenarlo en una comprobacion previa.

set -uo pipefail

DIR="${1:-.}"

echo "Buscando rutas absolutas en: $DIR"
echo

# Los patrones son los de CLAUDE.md. \\ cubre las rutas de Windows (C:\Users\...).
HALLAZGOS=$(grep -rn "/home/\|/Users/\|C:\\\\\|/sessions/\|/mnt/" \
  --include="*.py" --include="*.js" --include="*.ipynb" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=__pycache__ \
  "$DIR" 2>/dev/null)

if [ -n "$HALLAZGOS" ]; then
  echo "$HALLAZGOS"
  echo
  echo "FALLO: hay rutas absolutas. Resuelvelas desde la ubicacion del script:"
  echo "  Python:  Path(__file__).resolve().parents[1]"
  echo "  Node:    path.resolve(__dirname, '..')"
  echo "  Markdown: rutas de imagen relativas"
  exit 1
fi

echo "OK: ninguna ruta absoluta."
