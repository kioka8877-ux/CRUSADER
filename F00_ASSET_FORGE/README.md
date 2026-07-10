# F00 ASSET FORGE

## Vue d'ensemble

Frégate de pré-production CRUSADER. Extrait des actifs visuels (PNG transparents, GIFs, clips) depuis des vidéos sources (NASA, NOAA, ESA, USGS, Internet Archive) via GitHub Actions.

**Coût : 0 token, 0 appel API IA, tout automatisé.**

## Rôles

| Rôle | Qui | Fait quoi |
|---|---|---|
| **Oracle** | L'agent | Trigger le workflow, gère le pipeline, confirme les outputs |
| **Opérateur** | L'humain | Parcourt la banque, choisit les actifs, valide l'assemblage |

## Structure

```
F00_ASSET_FORGE/
├── CODEBASE/
│   ├── crs_f00_ingest.py      # Download vidéo (yt-dlp / NASA API / local)
│   ├── crs_f00_extract.py     # FFmpeg batch → frames + GIFs + clips
│   ├── crs_f00_process.py     # Rembg + chroma key (détourage)
│   ├── crs_f00_index.py       # Auto-indexation dans index.json
│   └── crs_f00_assemble.py    # Composite (personnage + décor → visuel final)
├── BANK_A_CHARACTERS/          # PNG transparents (Rembg) — classés par pose
├── BANK_B_NATURE/              # Feu, espace, météo, eau, fumée (GIFs + PNG)
├── BANK_C_BACKGROUNDS/         # Décors (PNG direct, sans traitement)
├── BANK_D_CLIPS/               # Clips vidéo courts (MP4)
├── index.json                  # Catalogue auto-généré
└── README.md                   # Ce fichier
```

## Pipeline

```
1. INGEST   — yt-dlp télécharge la vidéo source sur le runner GitHub Actions
2. EXTRACT  — FFmpeg extrait en batch : frames (1/sec), GIFs (2-5s), clips (5-10s)
3. PROCESS  — Rembg (personnages/objets) ou chroma key (feu/fumée fond noir) ou rien (décors)
4. INDEX    — index.json mis à jour automatiquement avec métadonnées de chaque actif
5. COMMIT   — Tout est commité sur la branche f00-asset-forge
```

## Sources vidéo privilégiées

| Source | Contenu | Accès |
|---|---|---|
| NASA SVS | Espace, planètes, lancements, phénomènes cosmiques | https://svs.gsfc.nasa.gov |
| NOAA / NWS | Météo satellite, ouragans, orages, nuages | https://www.nnvl.noaa.gov |
| ESA | Espace, Terre vue de l'espace | https://www.esa.int |
| USGS | Volcans, géologie, paysages | https://www.usgs.gov |
| Internet Archive | Films anciens, documentaires, footage historique | https://archive.org |

## Workflow GitHub Actions

Le workflow `f00_asset_forge.yml` est trigger par l'oracle via `workflow_dispatch`.

### Inputs

| Input | Description | Défaut |
|---|---|---|
| `video_urls` | URLs séparées par virgules | (obligatoire) |
| `mode` | `characters` \| `nature` \| `backgrounds` \| `all` | `all` |
| `extract_fps` | Frames par seconde | `1` |
| `gif_duration` | Durée GIFs en secondes | `3` |
| `clip_duration` | Durée clips MP4 en secondes | `8` |

## Flux Oracle → Opérateur

```
Oracle trigger workflow (URLs NASA/NOAA)
    ↓
GitHub Actions : ingest → extract → process → index → commit
    ↓
Oracle confirme : "Bank mise à jour, X PNGs + Y GIFs ajoutés"
    ↓
Opérateur parcourt BANK_*/ et index.json
    ↓
Opérateur choisit : "char_003 + bg_012 pour scène 1"
    ↓
Oracle lance l'assembleur → visuel final → gamma/SHARED/IN/images/
    ↓
Pipeline normal reprend (F02 → F03 → F04)
```

## Merge vers main

Conditions :
- Au moins 1 run complet réussi
- La banque contient des actifs utilisables
- L'assembleur a produit au moins 1 visuel final valide
- Le workflow est stable

Merge : `git checkout main → git merge f00-asset-forge → push`
