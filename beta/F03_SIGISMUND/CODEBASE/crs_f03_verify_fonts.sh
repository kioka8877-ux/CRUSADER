#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CRS_F03_VERIFY_FONTS.sh — Gardien des polices F03 SIGISMUND
# ═══════════════════════════════════════════════════════════════════════════════
# Usage  : ./crs_f03_verify_fonts.sh [DEST]
#   DEST : dossier destination (défaut: public/fonts)
#          peut être relatif (au CWD) ou absolu
# Exit 0 = TOUTES les polices vérifiées dans DEST
# Exit 1 = Police(s) manquante(s) — Run Remotion INTERDIT
# ═══════════════════════════════════════════════════════════════════════════════

DEST="${1:-public/fonts}"
FONT_SOURCE="${CRUSADER_FONTS:-/crusader-fonts}"

REQUIRED=(
  Cinzel-Regular
  Cinzel-Bold
  PlayfairDisplay-Regular
  PlayfairDisplay-Bold
  PlayfairDisplay-Italic
  PlayfairDisplay-BoldItalic
  Lato-Regular
  Lato-Bold
  Lato-Italic
  Oswald-Regular
  Oswald-SemiBold
  Oswald-Bold
  RobotoSlab-Regular
  RobotoSlab-Bold
  Inter-Regular
  Inter-Bold
  Inter-Black
)

echo ""
echo "═══════════════════════════════════════════════"
echo "  CRS_F03_VERIFY_FONTS"
echo "  Source : $FONT_SOURCE"
echo "  Dest   : $DEST"
echo "═══════════════════════════════════════════════"

# ── 1. Vérifier la source ────────────────────────────────────────────────────
echo ""
echo "[1/3] Inventaire source ($FONT_SOURCE) :"
if ! ls "$FONT_SOURCE"/*.woff2 >/dev/null 2>&1; then
  echo "  [FAIL] AUCUN fichier woff2 dans $FONT_SOURCE"
  echo "         → Image Docker corrompue ou mal construite"
  echo "         → Reconstruire : docker build + docker push"
  echo "═══════════════════════════════════════════════"
  exit 1
fi
SOURCE_COUNT=$(ls "$FONT_SOURCE"/*.woff2 | wc -l)
echo "  $SOURCE_COUNT fichiers woff2 disponibles"

# ── 2. Copier vers destination ───────────────────────────────────────────────
echo ""
echo "[2/3] Copie vers $DEST :"
mkdir -p "$DEST"
cp "$FONT_SOURCE"/*.woff2 "$DEST/"
COPIED=$(ls "$DEST"/*.woff2 2>/dev/null | wc -l)
echo "  $COPIED fichiers copiés"

# ── 3. Vérifier chaque police requise ───────────────────────────────────────
echo ""
echo "[3/3] Vérification des ${#REQUIRED[@]} polices requises :"
ERRORS=0
for NAME in "${REQUIRED[@]}"; do
  FILE="$DEST/${NAME}.woff2"
  if [ -f "$FILE" ]; then
    SIZE=$(du -h "$FILE" 2>/dev/null | cut -f1)
    echo "  [OK]   ${NAME}.woff2 — ${SIZE}"
  else
    echo "  [FAIL] ${NAME}.woff2 — ABSENT"
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "  POLICES OK — ${#REQUIRED[@]}/${#REQUIRED[@]} vérifiées dans $DEST/"
  echo "═══════════════════════════════════════════════"
  exit 0
else
  echo "  POLICES FAIL — $ERRORS police(s) manquante(s)"
  echo "  Run Remotion interdit — résoudre avant relance"
  echo "═══════════════════════════════════════════════"
  exit 1
fi
