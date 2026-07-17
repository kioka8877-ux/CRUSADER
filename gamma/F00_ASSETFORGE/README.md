# F00 ASSETFORGE

## Vue d'ensemble

Frégate de génération d'images IA pour CRUSADER. Produit des images de style cohérent
à partir d'une vidéo de référence et des segments Whisper (timing.json).

**3 phases, zéro compute local pour la génération :**
- Phase 0 : Extraction de style (sandbox, vision API)
- Phase 1 : Génération de prompts (sandbox, LLM)
- Phase 2 : Génération d'images (Kaggle GPU T4, FLUX.1-schnell)

**Modèle : FLUX.1-schnell** — 2-4s/image sur T4, licence Apache 2.0, gratuit, HuggingFace.

## Position dans le pipeline

```
--start
  └── F01A (silences) → F01B (Whisper) → timing.json
          ↓
      [GATE G1.5 — NOUVEAU]
          ↓
      F00 ASSETFORGE
        Phase 0 : Style extraction (sandbox, vision)
        Phase 1 : Prompt generation (sandbox, LLM)
        Phase 2 : Image generation (Kaggle GPU)
          ↓
      SHARED/IN/images/ alimenté
          ↓
  --gate G2 → F02 CASTELLAN (viewer roadmap)
```

## Structure

```
gamma/F00_ASSETFORGE/
├── IN/
│   └── reference_video.mp4       ← fourni par l'opérateur
├── OUT/
│   ├── style_prompt.txt          ← Phase 0 output
│   ├── prompts_manifest.json     ← Phase 1 output
│   └── images/                   ← Phase 2 output (avant commit vers SHARED)
├── CODEBASE/
│   ├── crs_f00_phase0.py         ← extraction style (ffmpeg + vision API)
│   ├── crs_f00_phase1.py         ← génération prompts (LLM)
│   └── f00_assetforge_kaggle.ipynb ← notebook Kaggle (Phase 2)
└── README.md                     ← ce fichier
```

## Phase 0 — Style Extraction

```bash
python CODEBASE/crs_f00_phase0.py
```

- FFmpeg extrait 12 frames (1280px max, évite 5s début/fin)
- Frames envoyées au modèle vision via AI Gateway
- Output : `OUT/style_prompt.txt` (150-300 mots)

## Phase 1 — Prompt Generation

```bash
python CODEBASE/crs_f00_phase1.py --mode GROUPED --format HORIZONTAL
```

- Lit `timing.json` + `style_prompt.txt`
- Mode GROUPED : 5-8 groupes de 3-6 segments
- Mode 1:1 : 1 image par segment
- Output : `OUT/prompts_manifest.json`

## Phase 2 — Image Generation (Kaggle)

Déclenchée via GitHub Actions (`f00_assetforge.yml`).

- Mode TEST : 1 seule image (gate G1.5)
- Mode FULL : batch complet (chunk si >60 images)
- FLUX.1-schnell sur GPU T4
- Images commitées dans `SHARED/IN/images/`

## Credentials requis

| Secret GitHub | Usage |
|---|---|
| `GH_TOKEN` | upload/download artifacts |
| `KAGGLE_USERNAME` | push notebook Kaggle |
| `KAGGLE_KEY` | API key Kaggle |
| `AI_GATEWAY_BASE_URL` | Phase 0 et 1 (sandbox) |
| `AI_GATEWAY_API_KEY` | Phase 0 et 1 (sandbox) |

## Conventions respectées

- Nommage images : `MM_SS_mmm.png` (timestamp du premier segment)
- Zéro texte dans les images (sous-titres ajoutés par F03)
- Style cohérent sur toutes les images
- Stdlib Python pour le code local
- `permissions: contents: write` dans le workflow
- Ledger mis à jour avant chaque gate
- F00 alimente uniquement `SHARED/IN/images/` — zéro impact sur F01-F05
