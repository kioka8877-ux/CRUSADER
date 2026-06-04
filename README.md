# CRUSADER
## Pipeline Automatisé de Production Vidéo — Style Stickman Whiteboard

> *"No pity. No remorse. No fear."* — Black Templars

---

## VICTORIA AETERNA — AU NOM DE L'EMPEREUR

**CAMP_02 terminée — 2026-06-04**
Pipeline CRUSADER F01A → F01B → F02 → F03 → F04 validé en conditions de production réelles.
La croisade est en marche. Que l'Omnissiah guide chaque octet.

```
[████████████████] PIPELINE COMPLET — 4/4 FRÉGATES SCELLÉES
[████████████████] CAMP_01 VALIDÉE — 2026-05-27
[████████████████] CAMP_02 VALIDÉE — 2026-06-04
```

---

## Présentation

**CRUSADER** est un pipeline de production vidéo automatisé en ligne de commande (headless), conçu pour générer des vidéos animées au style **Stickman Whiteboard** (tableau blanc / dessin fait main).

- **Format** : Vertical 1080×1920 (Shorts / Reels) ou Horizontal 1920×1080 (Long-form)
- **Objectif** : 10+ vidéos par jour
- **Coût** : Entièrement gratuit (Colab + GitHub Actions + Drive + outils open-source)
- **Exécution** : Google Colab (CPU/GPU T4) + GitHub Actions (rendu parallèle) — le PC est une télécommande

---

## Architecture — Les 4 Frégates

```
SHARED/
  audio_clean.mp3
  images/
       │
       ▼
F01A_CASTELLAN-AUDIO → audio_clean.mp3   [Nettoyage silences]
       │
       ▼
F01_GRIMALDUS → timing.json
       │
       ▼
F02_CASTELLAN → roadmap.json   [Viewer HTML — config créative]
       │
       ▼
F03_SIGISMUND → short_render.mp4   [GitHub Actions — rendu parallèle]
       │
       ▼
F04_HELBRECHT → youtube_short.mp4  [Camouflage FFmpeg — validation]
```

| Frégate | Nom | Rôle |
|---------|-----|------|
| F01A | CASTELLAN-AUDIO | Nettoyage audio (suppression silences) → `audio_clean.mp3` |
| F01 | GRIMALDUS | Transcription audio via faster-whisper → `timing.json` |
| F02 | CASTELLAN | Config créative + viewer HTML → `roadmap.json` |
| F03 | SIGISMUND | Rendu Remotion parallèle (GitHub Actions) → `short_render.mp4` |
| F04 | HELBRECHT | Camouflage FFmpeg + assemblage final → `youtube_short.mp4` |

---

## Pile Technologique

- **Nettoyage audio** : Flask + pydub (Colab CPU)
- **Transcription** : faster-whisper (Colab GPU T4 ou CPU)
- **Rendu vidéo** : Remotion (React/Node.js) — rendu parallèle sur GitHub Actions (10 workers)
- **Assemblage & camouflage** : FFmpeg (re-encode H.264 CRF18, loudnorm -14 LUFS, wipe métadonnées)
- **Config & Preview** : Flask + HTML natif Colab
- **Stockage** : Google Drive (`DRIVE_CRUSADER/`)
- **Environnement** : Google Colab + GitHub Actions

---

## Axiomes du Projet

1. **Gratuit** — Zéro API payante, zéro dépendance cloud commerciale
2. **30 fps** — Cible unique, configurable dans le JSON meta
3. **Dual format** — Vertical (Shorts) et Horizontal (Long-form) via un seul paramètre
4. **Colab-first** — Orchestration dans Colab, rendu lourd sur GitHub Actions, le PC est une télécommande
5. **Isolation des frégates** — Chaque frégate ne connaît que son IN/ et son OUT/
6. **Transfert validé** — Tout transit inter-frégate passe par `CRS_CUSTOS.py`
7. **Camouflage total** — F04 efface toute empreinte d'outil (Remotion, FFmpeg, IA) avant upload YouTube

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
├── CRS_CUSTOS.py           ← Gardien inter-frégate (validation transferts)
├── CRS_CODEDUMP.py         ← Export snapshot du codebase
├── TRACKING/
│   ├── CRUSADER_CAMPAIGN_LOG.md
│   └── CRUSADER_TRANSFER_LOG.md
├── SHARED/
│   └── .gitkeep
├── METAPROMPTS/
│   ├── META_01_SCRIPT.md   ← Script viral via Claude
│   └── META_02_VISUELS.md  ← Visuels Gemini 3.1 Pro
├── F01_GRIMALDUS/
│   └── CODEBASE/
├── F02_CASTELLAN/
│   └── CODEBASE/
├── F03_SIGISMUND/
│   └── CODEBASE/           ← incl. f03_render.yml (GitHub Actions)
└── F04_HELBRECHT/
    └── CODEBASE/
```

---

*Nomenclature tirée du lore Warhammer 40K — Légion des Black Templars.*
