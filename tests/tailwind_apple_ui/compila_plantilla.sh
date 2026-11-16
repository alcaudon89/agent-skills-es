#!/usr/bin/env bash
# Compila references/theme.css con la CLI oficial de Tailwind v4 y comprueba que:
# - los tokens semánticos y las utilidades glass-* generan clases;
# - la paleta y las sombras por defecto quedan anuladas;
# - están las alternativas de transparencia y de navegador sin backdrop-filter;
# - el script de revisión no da SIN-ALT-TRANSP sobre la plantilla.
# Uso (desde la raíz del repo): bash tests/tailwind_apple_ui/compila_plantilla.sh
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
TEMA="$RAIZ/skills/tailwind-apple-ui/references/theme.css"
SCRIPT="$RAIZ/skills/tailwind-apple-ui/scripts/revisa_estilos.py"
[ -f "$TEMA" ] || { echo "FALLO: no existe $TEMA"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp "$TEMA" "$TMP/theme.css"
cat > "$TMP/in.css" <<'EOF'
@import "tailwindcss";
@import "./theme.css";
@source "./index.html";
EOF
cat > "$TMP/index.html" <<'EOF'
<nav class="glass-bar text-label">x</nav>
<main class="bg-background text-title-1 rounded-lg shadow-md bg-gray-500 shadow-2xl"></main>
EOF

(cd "$TMP" && npm init -y >/dev/null && npm install --silent --no-audit --no-fund tailwindcss@4 @tailwindcss/cli@4 \
  && npx tailwindcss -i in.css -o out.css >/dev/null 2>"$TMP/err.txt") \
  || { cat "$TMP/err.txt"; echo "FALLO: no compila"; exit 1; }

fallos=0
debe()    { grep -qF -- "$1" "$TMP/out.css" && echo "ok   contiene $1" || { echo "FALLO falta $1"; fallos=1; }; }
no_debe() { grep -qF -- "$1" "$TMP/out.css" && { echo "FALLO sobra $1"; fallos=1; } || echo "ok   no contiene $1"; }

debe ".bg-background"
debe ".text-label"
debe ".glass-bar"
debe ".text-title-1"
debe ".rounded-lg"
debe ".shadow-md"
no_debe ".bg-gray-500"
no_debe ".shadow-2xl"
debe "prefers-reduced-transparency"
debe "@supports not"
debe "prefers-color-scheme: dark"

rm "$TMP/out.css"
if python3 -I "$SCRIPT" "$TMP" | grep -q "SIN-ALT-TRANSP"; then
  echo "FALLO el script da SIN-ALT-TRANSP sobre la plantilla"; fallos=1
else
  echo "ok   el script no da SIN-ALT-TRANSP"
fi

[ "$fallos" = 0 ] && echo "PLANTILLA OK" || { echo "PLANTILLA CON FALLOS"; exit 1; }
