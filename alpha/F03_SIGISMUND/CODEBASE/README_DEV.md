# F03 SIGISMUND — README DEV
## Rendu Remotion → short_render.mp4

---

## Rôle

SIGISMUND prend `timing.json` (F01), `roadmap.json` (F02), `audio_clean.mp3` et `images/`,
et produit `short_render.mp4` via **Remotion** (React → vidéo).
Chaque segment de la timeline est rendu avec son image (Ken Burns), ses sous-titres synchronisés,
un fond papier avec grain animé et vignetage.

---

## Stack

| Outil | Version | Rôle |
|-------|---------|------|
| Node.js | >= 18 | Runtime JS |
| Remotion | ^4.0.0 | React → vidéo |
| React | ^18.3.1 | Composants vidéo |
| Chromium | système | Rendu headless |
| Python | 3.10+ | Setup + orchestration |

---

## Structure du projet Remotion

```
F03_SIGISMUND/CODEBASE/
├── package.json
├── remotion.config.js
├── src/
│   ├── index.jsx           ← registerRoot(Root)
│   ├── Root.jsx            ← Composition + calculateMetadata
│   ├── Main.jsx            ← Audio + Background + Sequences
│   └── components/
│       ├── Scene.jsx       ← Image Ken Burns + Subtitle
│       ├── Subtitle.jsx    ← Texte + mots forts + fondu
│       └── Background.jsx  ← Couleur + grain + vignette + Google Fonts
├── crs_f03_sigismund.py
├── CRS_F03.ipynb
└── README_DEV.md
```

---

## Inputs / Outputs

```
F03_SIGISMUND/
├── IN/
│   ├── timing.json         ← Produit par F01 GRIMALDUS
│   ├── roadmap.json        ← Produit par F02 CASTELLAN
│   ├── audio_clean.mp3     ← Piste audio de la vidéo
│   └── images/             ← Images stickman (1.png, 2.png, ...)
├── OUT/
│   └── short_render.mp4    ← Vidéo rendue, prête pour F04
└── CODEBASE/
    └── ...
```

---

## Fonctionnement Remotion

### Root.jsx — calculateMetadata
Charge `timing.json` + `roadmap.json` depuis `public/` via `fetch(staticFile(...))`.
Déduit dynamiquement : `durationInFrames`, `fps`, `width`, `height`.

### Main.jsx — Composition principale
- Fond permanent : `<Background style={roadmap.style} />`
- Pour chaque `timeline[i]` : `<Sequence from={start_frame} durationInFrames={dur}>`
  contenant `<Scene segment={seg} timingSeg={timing.segments[i]} />`
- Piste audio : `<Audio src={staticFile('audio_clean.mp3')} />`

### Scene.jsx — Segment
- Image de fond avec effet Ken Burns (scale 1.0→1.04, translateX 0→-10px)
- `<Subtitle />` par dessus

### Subtitle.jsx — Sous-titres
- Fondu entrée/sortie sur 4 frames
- Mots forts (`is_strong: true`) : police accent (Playfair Display Italic) + couleur accent
- Mots normaux : police principale (Cinzel)
- Position : top / center / bottom (depuis roadmap.style)

### Background.jsx — Fond
- `background_color` en fond
- Grain animé via SVG `feTurbulence` (seed change toutes les 3 frames)
- Vignette radiale (si `vignette: true`)
- Injection Google Fonts (Cinzel + Playfair Display)

---

## Commande de rendu (hors Colab)

```bash
# Copier les assets dans public/ d'abord
python crs_f03_sigismund.py \
  --input   /path/to/F03_SIGISMUND/IN/ \
  --output  /path/to/F03_SIGISMUND/OUT/ \
  --project /path/to/F03_SIGISMUND/CODEBASE/ \
  --gl      swangle
```

---

## Rendu direct Remotion (debug)

```bash
cd F03_SIGISMUND/CODEBASE/
npm install
npx remotion render src/index.jsx CrusaderShort out.mp4 --gl=swangle
```

---

## Validation CUSTOS

```bash
# Avant de lancer (vérifier timing.json + roadmap.json + audio + images/)
python CRS_CUSTOS.py --frigate F03 --mode check-out

# Après rendu (vérifier short_render.mp4 > 100 KB)
python CRS_CUSTOS.py --frigate F03 --mode check-in
```

---

## Notes de production

- `--gl swangle` est obligatoire en Colab (pas de GPU OpenGL disponible).
- Google Fonts requiert un accès internet pendant le rendu — Colab en dispose.
- Si `image_file` est `null` pour un segment, le segment affiche uniquement la couleur de fond.
- Le `grain_seed` tourne sur 64 valeurs toutes les 3 frames → grain animé sans boucle visible.
