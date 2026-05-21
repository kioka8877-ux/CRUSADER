# F04 HELBRECHT — README DEV
## Remux FFmpeg → final_master.mp4

---

## Rôle

HELBRECHT prend `short_render.mp4` (F03) et `timing.json` (F01),
effectue un **remux FFmpeg sans réencodage** avec injection de métadonnées
et optimisation streaming (`+faststart`), et produit `final_master.mp4`
prêt au téléchargement et à l'upload (YouTube, TikTok, Reels).

---

## Stack

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.10+ | Orchestration |
| FFmpeg | >= 4.0 | Remux + métadonnées |
| ffprobe | >= 4.0 | Analyse vidéo finale |

---

## Structure

```
F04_HELBRECHT/CODEBASE/
├── crs_f04_helbrecht.py    ← Script principal (remux + probe)
├── CRS_F04.ipynb           ← Notebook Colab (point d'entrée opérateur)
└── README_DEV.md           ← Ce fichier
```

---

## Inputs / Outputs

```
F04_HELBRECHT/
├── IN/
│   ├── short_render.mp4    ← Produit par F03 SIGISMUND
│   └── timing.json         ← Produit par F01 GRIMALDUS
└── OUT/
    └── final_master.mp4    ← Vidéo finale, prête à l'upload
```

---

## Fonctionnement

### 1. Vérification ffmpeg
Vérifie que `ffmpeg` est accessible. Préinstallé sur Colab.

### 2. Lecture timing.json
Extrait la clé `meta` pour construire les métadonnées FFmpeg :

| Clé meta | Métadonnée FFmpeg | Défaut |
|----------|-------------------|--------|
| `title` | `title` | `CRUSADER_SHORT` |
| `comment` | `comment` | `Pipeline CRUSADER — Frégate HELBRECHT` |
| `fps` | dans `description` | `30` |
| `format` | dans `description` | `vertical` |

### 3. Remux FFmpeg
Commande générée :
```bash
ffmpeg -y \
  -i short_render.mp4 \
  -c:v copy \
  -c:a copy \
  -movflags +faststart \
  -metadata title="..." \
  -metadata comment="..." \
  -metadata description="..." \
  -metadata date="YYYY-MM-DD" \
  -metadata encoder="CRUSADER v1.0 — F04 HELBRECHT" \
  final_master.mp4
```

**`-c:v copy -c:a copy`** : aucun réencodage → rapide (10–60 s selon taille).
**`+faststart`** : MOOV atom en début de fichier → lecture streaming instantanée.

### 4. Vérification sortie
Vérifie que `final_master.mp4` existe et dépasse 100 KB.

### 5. Probe vidéo
`ffprobe` affiche : durée, codec vidéo, résolution, codec audio, sample rate.

---

## Commande directe (hors Colab)

```bash
python crs_f04_helbrecht.py \
  --input  /path/to/F04_HELBRECHT/IN/ \
  --output /path/to/F04_HELBRECHT/OUT/
```

---

## Validation CUSTOS

```bash
# Avant remux (vérifier short_render.mp4 + timing.json dans IN/)
python CRS_CUSTOS.py --frigate F04 --mode check-out

# Après remux (vérifier final_master.mp4 > 100 KB dans OUT/)
python CRS_CUSTOS.py --frigate F04 --mode check-in
```

---

## Notes de production

- FFmpeg est préinstallé sur Colab — pas d'installation nécessaire en général.
- Le remux est sans perte de qualité (copie de flux).
- `+faststart` est indispensable pour les plateformes (YouTube détecte la présence du MOOV atom).
- Si `timing.json` ne contient pas de clé `title` dans `meta`, le titre par défaut `CRUSADER_SHORT` est utilisé — cela ne bloque pas le remux.
- `final_master.mp4` est le produit final du pipeline CRUSADER. Aucune frégate ne dépend de F04.
