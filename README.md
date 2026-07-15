# CRUSADER
## Pipeline Automatisé de Production Vidéo

> *"No pity. No remorse. No fear."* — Black Templars

---

## VICTORIA AETERNA — AU NOM DE L'EMPEREUR

```
[████████████████] CAMP_01 VALIDÉE — 2026-05-27
[████████████████] CAMP_02 VALIDÉE — 2026-06-04
[████████████████] RUBICON FRANCHI — 2026-06-18
[████░░░░░░░░░░░░] CAMP_03 EN COURS — CRUSADER BETA
```

---

## Architecture — Les 5 Frégates (GitHub Actions Edition)

```
SHARED/IN/
  audio_raw.mp3 + images/
        │
        ▼
  [Gate G1 → opérateur vérifie]
        │
F01 GRIMALDUS  → timing.json         [GH Actions — FFmpeg silences + Whisper]
        │
  [Gate G2 → opérateur valide viewer]
        │
F02 CASTELLAN  → roadmap.json        [Sandbox stdlib — viewer HTML port 8080]
        │
  [Gate G3 → opérateur vérifie render]
        │
F03 SIGISMUND  → short_render.mp4    [GH Actions — Remotion Docker 10 workers]
        │
  [Gate G4 → opérateur valide final]
        │
F04 HELBRECHT  → youtube_final.mp4   [GH Actions — FFmpeg assemblage loudnorm]
        │
F05 LUTHER     → clean_final.mp4     [GH Actions — strip métadonnées, auto après F04]
```

| Frégate | Nom | Rôle | Runner |
|---------|-----|------|--------|
| F01 | GRIMALDUS | FFmpeg silences + Whisper → `timing.json` | GitHub Actions |
| F02 | CASTELLAN | Viewer HTML config → `roadmap.json` | Sandbox stdlib (port 8080) |
| F03 | SIGISMUND | Remotion render parallèle → `short_render.mp4` | GitHub Actions (Docker custom, 10 workers) |
| F04 | HELBRECHT | FFmpeg assemblage + loudnorm → `youtube_final.mp4` | GitHub Actions |
| F05 | LUTHER | Strip métadonnées empreinte zéro → `clean_final.mp4` | GitHub Actions (auto après F04) |

**Doctrine :** Sandbox = télécommande uniquement. Zéro compute local. 4 gates opérateur.

---

## Spec Visuelle CRUSADER BETA — Verrouillée 2026-06-20

**Paradigme caméra dans un monde 2D** (remplace le modèle composition d'écran CAMP_01/02)

- **Monde 2D** : tous les visuels posés à des ancres fixes dans l'espace
- **Visuel actif N** : plein cadre (100%), sync voix en temps réel
- **Visuel suivant N+1** : ancré top-right ou bottom-right (~20% visible avant le voyage), alternance stricte
- **Voyage caméra** : la caméra se déplace vers l'ancre N+1 via ressort — le visuel N reste en place
- **Texte/titre** : attaché à la caméra, suit le voyage
- **Flèche tactique** : pointe dynamiquement vers l'ancre active

| Paramètre | Valeur |
|-----------|--------|
| Ressort | mass 0.4 / stiffness 210 / damping 14 / 10 frames |
| Regard | AVAL — N+1 (index direct F03) |
| Seuil terminal | FANTÔME — dernier visuel reste visible |
| Types média | static\_image \| video\_clip \| gif (@remotion/gif) |
| Règle SFX | `index < 3` : SFX à chaque apparition — puis `index % 3 === 0` |

---

## Pile Technologique

| Composant | Technologie |
|-----------|-------------|
| Nettoyage audio | FFmpeg (GH Actions) |
| Transcription | faster-whisper medium, CPU int8 fallback |
| Rendu vidéo | Remotion React/Node.js — Docker custom `crusader-remotion:latest` |
| Assemblage | FFmpeg CRF18, loudnorm -14 LUFS, +faststart |
| Strip métadonnées | FFmpeg `-c copy -map_metadata -1` (F05 LUTHER) |
| Stockage assets | GitHub Release |
| Orchestration | Python stdlib (zéro pip) |

---

## Commandes

```bash
# Nouveau sandbox
git clone https://ghp_TOKEN@github.com/kioka8877-ux/CRUSADER.git
export GH_TOKEN=ghp_TOKEN

# Production
python CRS_EXECUTEUR.py --start --title "Mon Sujet"   # → Gate G1
python CRS_EXECUTEUR.py --gate G2                      # → Gate G2
python CRS_EXECUTEUR.py --gate G3                      # → Gate G3
python CRS_EXECUTEUR.py --gate G4                      # → Gate G4
python CRS_EXECUTEUR.py --close                        # → Victoria Aeterna
```

---

## Axiomes

1. **Sandbox = télécommande** — Zéro calcul local, tout sur GitHub Actions
2. **4 gates opérateur** — Décisions humaines uniquement aux points de contrôle
3. **Gratuit** — GitHub Actions 2000 min/mois, Docker custom, zéro API payante
4. **Isolation des frégates** — Chaque frégate lit son IN/, écrit son OUT/
5. **Empreinte zéro** — F05 LUTHER efface toute trace d'outil avant livraison

---

## Structure du Repo

```
CRUSADER/
├── README.md
├── CRS_COLD_START.md       ← Reprendre après crash sandbox
├── CRS_EXECUTEUR.py        ← Orchestrateur (télécommande)
├── CRS_CUSTOS.py           ← Gardien inter-frégate (validation)
├── CRS_F02_SERVER.py       ← Serveur viewer F02 (stdlib, port 8080)
├── crs_ledger.json         ← État de la production en cours
├── TRACKING/
│   ├── CRUSADER_CAMPAIGN_LOG.md
│   └── CRUSADER_TRANSFER_LOG.md
├── SHARED/
│   └── IN/                 ← audio_raw.mp3 + images/ (commités dans repo)
├── METAPROMPTS/
├── F01_GRIMALDUS/CODEBASE/
├── F02_CASTELLAN/CODEBASE/
├── F03_SIGISMUND/CODEBASE/ ← src/ React + .github/workflows/f03_render.yml
├── F04_HELBRECHT/CODEBASE/
├── F05_LUTHER/CODEBASE/
└── .github/workflows/
    ├── f01_grimaldus.yml
    ├── f03_render.yml
    ├── f04_helbrecht.yml
    └── docker-build.yml
```

---

*Nomenclature tirée du lore Warhammer 40K — Légion des Black Templars.*

---

## DELTA — Mode de Production Validé (2026-07-15)

```
[████████████████] DELTA-TEST3 VALIDÉE — 2026-07-15
F00 ✅  F01 ✅  F02 ✅  F03 ✅  F04 ✅  F05 ✅
```

Pipeline CRUSADER gamma validé en production sur la branche `delta-test3`, copié vers `delta/` sur main.

| Frégate | Statut | Description |
|---------|--------|-------------|
| F00 | ✅ | Assets pré-générés (93 visuels) |
| F01 | ✅ | Audio + transcription (82 segments, 4:27) |
| F02 | ✅ | Preview + UI curation + injecteur de visuels |
| F03 | ✅ | Render CrusaderDelta 8030 frames (10/10 chunks) |
| F04 | ✅ | Camouflage + finalisation YouTube |
| F05 | ✅ | Publication |

**Composition** : `CrusaderDelta` (DeltaMain.jsx) — capsules WorldScene + miniatures announce + sous-titres mot par mot

**Vidéo finale** : 1920×1080, 4:27, 101.6 MB
**Drive** : https://drive.google.com/file/d/1Lx-e7I4aS32Y7aFZSjm-hP-LHtakr2Q_/view

**Fixes appliqués** :
- `public/images/` subdirectory pour `staticFile()`
- Composition `CrusaderDelta` (capsules + announce + subtitles)
- UI thumbnails (82 micro-previews)
- Auto-sync base64 (zéro aller-retour curation)

**Mode delta** : utiliser `mode: delta` dans les workflows GitHub Actions.
