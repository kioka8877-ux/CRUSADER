# F04 HELBRECHT v2 — README DEV
## Camouflage universel + Finalisation YouTube

> **SCELLÉE — 2026-05-27 (CAMP_01) | CAMP_02 VALIDÉE — 2026-06-04**
> *"No pity. No remorse. No fear."* — Black Templars

---

## Rôle

HELBRECHT est la **frégate universelle de finalisation vidéo**.

Elle prend `short_render.mp4` (F03) et `timing.json` (F01), applique un
**camouflage complet** (re-encode + wipe métadonnées + normalisation audio),
et produit une vidéo propre prête à l'upload YouTube — sans aucune empreinte d'outil,
d'IA, ou de pipeline de production.

**Principe SpaceX** : cette frégate est identique dans tous les projets.
Seul `timing.json` change. Aucune modification de code entre niches.

---

## Stack

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.10+ | Orchestration |
| FFmpeg | >= 4.0 | Re-encode + camouflage + loudnorm |
| ffprobe | >= 4.0 | Analyse vidéo source et sortie |

---

## Structure

```
F04_HELBRECHT/CODEBASE/
├── crs_f04_helbrecht.py    ← Script principal v2 (universel)
├── CRS_F04.ipynb           ← Notebook Colab (point d'entrée opérateur)
└── README_DEV.md           ← Ce fichier
```

---

## Inputs / Outputs

```
F04_HELBRECHT/
├── IN/
│   ├── short_render.mp4        ← Produit par F03 SIGISMUND
│   └── timing.json             ← Produit par F01 GRIMALDUS
└── OUT/
    ├── youtube_short.mp4       ← Si format vertical (9:16)
    │     OU
    ├── youtube_long.mp4        ← Si format horizontal (16:9)
    └── rapport_f04.html        ← Rapport opérateur
```

---

## Schema timing.json (contrat d'interface)

```json
{
  "meta": {
    "title":            "Titre de la vidéo",
    "description":      "Description YouTube (optionnel)",
    "fps":              30,
    "format":           "vertical | horizontal",
    "duration_seconds": 59.0,
    "date":             "YYYY-MM-DD",
    "chapters": [
      { "t": 0,   "label": "Intro" },
      { "t": 15,  "label": "Partie 1" },
      { "t": 45,  "label": "Conclusion" }
    ]
  }
}
```

**Champs obligatoires** : aucun — tous ont des valeurs par défaut.
**Priorité** : les dimensions réelles de la vidéo priment sur `format`.

---

## Pipeline de traitement

### 1. Détection format automatique
`ffprobe` lit les dimensions de `short_render.mp4` :
- `hauteur > largeur` → **vertical** → `youtube_short.mp4`
- `largeur ≥ hauteur` → **horizontal** → `youtube_long.mp4`

### 2. QA pré-camouflage
Vérifie : durée cohérente, stream vidéo présent, stream audio présent, taille > 100 KB.
Bloque si la vidéo source est invalide.

### 3. Camouflage FFmpeg (cœur de la frégate)

Commande générée :
```bash
ffmpeg -y \
  -i short_render.mp4 \
  -map_metadata -1 \
  -metadata encoder= \
  -c:v libx264 -crf 18 -preset medium \
  -profile:v high -level 4.0 \
  -g 60 -keyint_min 60 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -af "loudnorm=I=-14:TP=-1:LRA=11" \
  -movflags +faststart \
  -metadata title="..." \
  -metadata date="YYYY-MM-DD" \
  youtube_short.mp4   # ou youtube_long.mp4
```

**Ce que ça efface :**
- `-map_metadata -1` : wipe total des tags container (encoder, software, encoding_tool, creation_time, etc.)
- `-metadata encoder=` : neutralise le tag `Lavf` réinjecté automatiquement par FFmpeg lors du muxing
- Re-encode H.264 : efface les fingerprints du stream vidéo (Remotion, OpenCV, etc.)
- Re-encode AAC : efface les fingerprints du stream audio (ElevenLabs, Suno, etc.)

**Ce que ça normalise :**
- GOP régulier 2s : structure identique à un montage Premiere/DaVinci
- Loudnorm -14 LUFS / -1 dBTP : standard YouTube, évite les flags d'audio anormal
- yuv420p : compatibilité maximale toutes plateformes

**Tags injectés (minimalistes) :**
- `title` : depuis timing.json
- `date` : depuis timing.json (ou today)
- Aucun autre tag — ni encoder, ni software, ni comment

### 4. Touch timestamp
Le timestamp système du fichier est aligné sur `meta.date` de timing.json.
Si non spécifié : date du jour.

### 5. QA post-camouflage
Vérifie en plus : aucun tag suspect résiduel, codec H.264, audio AAC 48kHz.

Liste complète des tags suspects détectés : `remotion`, `opencv`, `python`, `openai`, `runway`,
`stable-diffusion`, `suno`, `udio`, `elevenlabs`, `whisper`, `ffmpeg-python`, `moviepy`, `lavf`, `lavc`.

### 6. Chapters YouTube
Si `timing.json` contient un tableau `chapters`, génère le texte formaté :
```
00:00 Intro
00:15 Partie principale
01:30 Conclusion
```

### 7. Rapport HTML
Fichier `rapport_f04.html` : métriques vidéo, checklist QA, chapters, description YouTube.

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
# Avant (vérifier short_render.mp4 + timing.json dans IN/)
python CRS_CUSTOS.py --frigate F04 --mode check-out --drive-base /path/DRIVE

# Après (vérifier youtube_*.mp4 > 100 KB dans OUT/)
python CRS_CUSTOS.py --frigate F04 --mode check-in --drive-base /path/DRIVE
```

---

## Universalité — Utilisation dans un autre projet

F04 ne contient aucune référence au contenu ou à la niche dans sa logique.
Pour l'utiliser dans un projet différent (immobilier, fitness, etc.) :

1. Copiez le dossier `F04_HELBRECHT/` dans le nouveau projet
2. Le F01 du nouveau projet doit produire un `timing.json` conforme au schema ci-dessus
3. Le F03 du nouveau projet doit produire `short_render.mp4`
4. Lancez F04 — aucune modification de code nécessaire

---

## Historique des versions

| Date | Version | Changement |
|------|---------|------------|
| 2026-05-21 | v1 | Remux FFmpeg `-c copy` — rapide mais empreinte Remotion intacte |
| 2026-05-27 | v2 | Re-encode CRF18 + camouflage complet + loudnorm -14 LUFS + détection format auto. CAMP_01 validée. |
| 2026-06-04 | v2.1 | `-metadata encoder=` ajouté — neutralise le tag `Lavf` résiduel. `lavf`/`lavc` ajoutés dans SUSPICIOUS_TAGS. CAMP_02 validée. |

---

## Notes de production

- Re-encode CRF18 = qualité visuelle quasi-lossless mais fingerprint effacé.
- Sur Colab CPU, compter ~2–8 min selon durée vidéo. GPU non requis.
- `loudnorm` single-pass : précision suffisante pour production. Double-pass possible manuellement si besoin.
- Fichier de sortie : `youtube_short.mp4` (vertical) ou `youtube_long.mp4` (horizontal) — détection automatique par dimensions.
- Aucune frégate ne dépend de F04 — c'est le terminus du pipeline.
