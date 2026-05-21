# CRUSADER
## Pipeline Automatisé de Production Vidéo — Style Stickman Whiteboard

> *"No pity. No remorse. No fear."* — Black Templars

---

## Présentation

**CRUSADER** est un pipeline de production vidéo automatisé en ligne de commande (headless), conçu pour générer des vidéos animées au style **Stickman Whiteboard** (tableau blanc / dessin fait main).

- **Format** : Vertical 1080×1920 (Shorts / Reels) ou Horizontal 1920×1080 (Long-form)
- **Objectif** : 10+ vidéos par jour
- **Coût** : Entièrement gratuit (Colab + Drive + outils open-source)
- **Exécution** : Google Colab (GPU T4) — le PC est une télécommande

---

## Architecture — Les 4 Frégates

```
SHARED/
  audio_clean.mp3
  images/
       │
       ▼
F01_GRIMALDUS → timing.json
       │
       ▼
F02_CASTELLAN → roadmap.json   [Viewer HTML — config créative]
       │
       ▼
F03_SIGISMUND → short_render.mp4
       │
       ▼
F04_HELBRECHT → final_master.mp4  [Viewer vidéo — validation]
```

| Frégate | Nom | Rôle |
|---------|-----|------|
| F01 | GRIMALDUS | Transcription audio via faster-whisper → `timing.json` |
| F02 | CASTELLAN | Config créative + viewer HTML → `roadmap.json` |
| F03 | SIGISMUND | Rendu Remotion (animations + sous-titres) → `short_render.mp4` |
| F04 | HELBRECHT | Assemblage final FFmpeg + viewer validation → `final_master.mp4` |

---

## Pile Technologique

- **Transcription** : faster-whisper (local, gratuit, GPU Colab T4)
- **Rendu vidéo** : Remotion (React/Node.js)
- **Assemblage** : FFmpeg
- **Config & Preview** : Flask + HTML natif Colab
- **Stockage** : Google Drive (`DRIVE_CRUSADER/`)
- **Environnement** : Google Colab

---

## Axiomes du Projet

1. **Gratuit** — Zéro API payante, zéro dépendance cloud commerciale
2. **30 fps** — Cible unique, configurable dans le JSON meta
3. **Dual format** — Vertical (Shorts) et Horizontal (Long-form) via un seul paramètre
4. **Colab-first** — Tout tourne dans Colab, le PC est une télécommande
5. **Isolation des frégates** — Chaque frégate ne connaît que son IN/ et son OUT/
6. **Transfert validé** — Tout transit inter-frégate passe par `CRS_CUSTOS.py`

---

## Gardien de Flotte

```bash
python CRS_CUSTOS.py --frigate F01 --mode check-out
python CRS_CUSTOS.py --frigate F02 --mode check-in
```

---

## Structure du Repo

```
CRUSADER/
├── README.md
├── CRS_CUSTOS.py
├── TRACKING/
│   ├── CRUSADER_CAMPAIGN_LOG.md
│   └── CRUSADER_TRANSFER_LOG.md
├── SHARED/
│   └── .gitkeep
├── F01_GRIMALDUS/
│   └── CODEBASE/
├── F02_CASTELLAN/
│   └── CODEBASE/
├── F03_SIGISMUND/
│   └── CODEBASE/
└── F04_HELBRECHT/
    └── CODEBASE/
```

---

*Nomenclature tirée du lore Warhammer 40K — Légion des Black Templars.*
