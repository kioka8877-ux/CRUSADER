# ─────────────────────────────────────────────────────────────────────────────
# CRUSADER F03 — Image Docker de rendu
# Base : Node 20 Debian slim
# Contenu :
#   - Chromium + FFmpeg
#   - Polices système : Liberation Sans (Arial), Nimbus Sans (Helvetica),
#                        Arial Black (MS Core Fonts), Inter Black
#   - Polices Google Fonts woff2 embarquées dans /crusader-fonts/
#   - node_modules pré-installés dans /crusader-deps/
# Objectif : zéro téléchargement au moment du rendu. Workers prêts en <15s.
# ─────────────────────────────────────────────────────────────────────────────

FROM node:20-bookworm-slim

# ── 1. Outils système + polices système ───────────────────────────────────────
RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      # Rendu
      chromium \
      ffmpeg \
      # Utilitaires
      wget \
      ca-certificates \
      fontconfig \
      unzip \
      # Polices libres
      fonts-liberation \
      fonts-urw-base35 \
      fonts-freefont-ttf && \
    # MS Core Fonts (Arial, Arial Black, Times New Roman...) — EULA pré-acceptée
    echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | \
      debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ttf-mscorefonts-installer || \
    # Fallback si SourceForge bloque : on continue sans MS fonts (Liberation = secours)
    echo "[WARN] ttf-mscorefonts-installer échoué — Liberation Sans utilisé comme fallback Arial" && \
    fc-cache -fv && \
    rm -rf /var/lib/apt/lists/*

# ── 2. Polices Google Fonts (woff2 offline) ────────────────────────────────────
# Cinzel, Playfair Display, Lato, Oswald, Roboto Slab, Inter (Regular/Bold/Black)
COPY docker-fonts-dl.js /tmp/docker-fonts-dl.js
RUN node /tmp/docker-fonts-dl.js && \
    ls -lh /crusader-fonts/ && \
    echo "[FONTS] $(ls /crusader-fonts/ | wc -l) fichiers woff2 embarqués"

# ── 3. node_modules pré-installés ─────────────────────────────────────────────
WORKDIR /crusader-deps
COPY package.json package-lock.json* ./
RUN npm install && \
    echo "[DEPS] node_modules installés : $(du -sh node_modules | cut -f1)"

# ── 4. Variables d'environnement pour les workers ────────────────────────────
ENV CRUSADER_DEPS=/crusader-deps
ENV CRUSADER_FONTS=/crusader-fonts
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CHROMIUM_PATH=/usr/bin/chromium

# ── 5. Sanity check ──────────────────────────────────────────────────────────
RUN echo "=== CRUSADER IMAGE SANITY CHECK ===" && \
    node --version && \
    (chromium --version 2>/dev/null || echo "chromium non trouvé dans PATH standard") && \
    which ffmpeg && ffmpeg -version 2>&1 | head -1 && \
    ls /crusader-fonts/*.woff2 | wc -l && echo "fichiers woff2 OK" && \
    ls /crusader-deps/node_modules | wc -l && echo "modules node OK" && \
    echo "==================================="
# build 20260619T032241Z
