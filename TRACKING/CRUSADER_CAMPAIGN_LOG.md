# CRUSADER — CAMPAIGN LOG
## Carnet de Bord de Croisade

> *"We are the Emperor's will made manifest."*

---

## Statut de la Flotte

| Frégate | Nom | Rôle | Statut | Date de Scellement |
|---------|-----|------|--------|--------------------|
| F01 | GRIMALDUS | Transcription audio → timing.json | SCELLÉE — TEST PROD RÉUSSI | 2026-05-21 |
| F02 | CASTELLAN | Config créative + viewer → roadmap.json | SCELLÉE — TEST PROD RÉUSSI | 2026-05-21 |
| F03 | SIGISMUND | Rendu Remotion → short_render.mp4 | SCELLÉE — EN TEST PROD | 2026-05-21 |
| F04 | HELBRECHT | Assemblage FFmpeg → final_master.mp4 | SCELLÉE — EN ATTENTE F03 | 2026-05-21 |
| META | METAPROMPTS | Guides opérateur (script + visuels) | SCELLÉS — PRÊTS À L'EMPLOI | 2026-05-21 |

**Compteur de Guerre :**
```
[████] 4/4 frégates scellées
[██]   2/2 metaprompts scellés
[██░░] 2/4 tests de production réussis
```

---

## Flux de Données

```
SHARED/audio_clean.mp3 ──────────────────► F01 IN, F03 IN
SHARED/images/ ──────────────────────────► F02 IN, F03 IN

F01 GRIMALDUS  → timing.json ────────────► F02 IN, F03 IN, F04 IN
F02 CASTELLAN  → roadmap.json ───────────► F03 IN
F03 SIGISMUND  → short_render.mp4 ───────► F04 IN
F04 HELBRECHT  → final_master.mp4 ───────► Téléchargement opérateur
```

---

## Rites du Sang — Principes Gouvernants

1. **Gratuit** — Aucun API payant, aucune dépendance commerciale
2. **Colab-first** — Tout s'exécute sur Google Colab (GPU T4), le PC est une télécommande
3. **30 fps** — Cible fixe, encodée dans le JSON meta
4. **Dual format** — Vertical 1080×1920 (Shorts) et Horizontal 1920×1080 (Long-form)
5. **Isolation des frégates** — Chaque frégate opère en silo, lit son IN/, écrit son OUT/
6. **Transfert validé** — Tout transit inter-frégate passe par CRS_CUSTOS.py (check-out + check-in)

---

## Décisions de Forge (Axiomes)

| Date | Décision | Justification |
|------|----------|---------------|
| 2026-05-21 | Whisper local via faster-whisper | Gratuit, GPU T4 Colab disponible |
| 2026-05-21 | 30 fps fixe | Suffisant pour stickman whiteboard, TikTok/Reels ne valorise pas 60fps |
| 2026-05-21 | Format choisi en F02 | Paramètre créatif = décision éditoriale de l'opérateur |
| 2026-05-21 | Mots-clés via balisage [mot] | Option A : l'opérateur balise explicitement dans structure.json |
| 2026-05-21 | Viewer F02 via port natif Colab | Pas de ngrok, pas de tunnel externe |
| 2026-05-21 | CRS_CUSTOS en Python stdlib | Pas de pip, fonctionne dans tout env Colab |
| 2026-05-21 | Viewer F02 HTML natif sans dépendances JS | Pas de React, pas de CDN — fonctionne offline |
| 2026-05-21 | Remotion 4.x + --gl swangle | Rendu logiciel Colab, pas de GPU OpenGL requis |
| 2026-05-21 | calculateMetadata pour métadonnées dynamiques | Remotion 4.x — dimensions/durée issues des JSON |
| 2026-05-21 | FFmpeg remux sans réencodage (-c copy) | Pas de perte qualité, traitement 10-60s vs plusieurs minutes |
| 2026-05-21 | +faststart obligatoire | MOOV atom en tête de fichier — requis YouTube/TikTok/Reels |
| 2026-05-21 | Balisage [mots_forts] intégré dans META_01 | Continuité automatique vers F03 sans intervention manuelle |
| 2026-05-21 | MODE GROUPED / 1:1 dans META_02 | Flexibilité test vs prod, même prompt — juste changer le paramètre |
| 2026-05-22 | Unification SCRIPT_DIR → /content/crusader | Cohérence inter-frégates, F02/F03/F04 alignés sur F01 |

---

## Fil d'Ariane — Log Chronologique

| Date | Frégate | Phase | Action | Validé |
|------|---------|-------|--------|--------|
| 2026-05-21 | — | INIT | Création du repo CRUSADER sur GitHub | ✓ |
| 2026-05-21 | — | INIT | Structure des frégates initialisée | ✓ |
| 2026-05-21 | F01 | FORGE | Développement terminé : crs_f01_grimaldus.py + CRS_F01.ipynb | ✓ |
| 2026-05-21 | F02 | FORGE | Développement terminé : Flask server + HTML viewer + notebook | ✓ |
| 2026-05-21 | F03 | FORGE | Développement terminé : Remotion (6 fichiers src/) + notebook | ✓ |
| 2026-05-21 | F04 | FORGE | Développement terminé : crs_f04_helbrecht.py + CRS_F04.ipynb | ✓ |
| 2026-05-21 | META | FORGE | META_01_SCRIPT.md scellé — script viral + balisage [mots_forts] | ✓ |
| 2026-05-21 | META | FORGE | META_02_VISUELS.md scellé — visuels Gemini + MODE GROUPED/1:1 | ✓ |
| 2026-05-22 | F02/F03/F04 | CORRECTIF | Unification SCRIPT_DIR → /content/crusader (cells 6 & 8 par notebook) | ✓ |
| 2026-05-22 | F01 | TEST PROD | RÉUSSI — timing.json produit : 43 segments, 109.7s, audio_path renseigné | ✓ |
| 2026-05-22 | F02 | TEST PROD | RÉUSSI — roadmap.json produit : 43 segments, vertical 1080×1920, validated_by_magos | ✓ |
| 2026-05-22 | F03 | TEST PROD | En cours — roadmap.json transféré en F03/IN, lancement imminent | — |

---

## F01 — GRIMALDUS

**Composants :**
- `CRS_F01.ipynb` — Notebook Colab (point d'entrée opérateur)
- `crs_f01_grimaldus.py` — Script faster-whisper, détection mots forts

**IN :** `audio_clean.mp3`
**OUT :** `timing.json`

**Tests de production :**
- 2026-05-22 — RÉUSSI : 43 segments détectés, durée 109.7s, `audio_path` correctement renseigné dans meta

---

## F02 — CASTELLAN

**Composants :**
- `CRS_F02.ipynb` — Notebook Colab (point d'entrée opérateur)
- `crs_f02_castellan.py` — Serveur Flask REST (port natif Colab)
- `crs_f02_viewer.html` — Interface HTML interactive (mapping images, style sous-titres, format)
- `README_DEV.md` — Documentation développeur

**IN :** `timing.json`, `images/`
**OUT :** `roadmap.json`

**Tests de production :**
- 2026-05-22 — RÉUSSI : roadmap.json produit — 43 segments, format vertical 1080×1920, 30fps, 7 images assignées, `validated_by_magos: true`
- CUSTOS check-out : VALIDATION OK
- CUSTOS check-in : VALIDATION OK

---

## F03 — SIGISMUND

**Composants :**
- `CRS_F03.ipynb` — Notebook Colab (point d'entrée opérateur)
- `crs_f03_sigismund.py` — Setup assets + lancement rendu Remotion
- `package.json` — Dépendances Node.js (Remotion 4.x + React 18)
- `remotion.config.js` — Configuration Remotion
- `src/index.jsx` — Enregistrement Root
- `src/Root.jsx` — Composition (calculateMetadata dynamique)
- `src/Main.jsx` — Audio + Background + Sequences
- `src/components/Scene.jsx` — Image Ken Burns + Subtitle
- `src/components/Subtitle.jsx` — Texte + mots forts + fondu
- `src/components/Background.jsx` — Fond + grain + vignette + Google Fonts
- `README_DEV.md` — Documentation développeur

**IN :** `timing.json`, `roadmap.json`, `audio_clean.mp3`, `images/`
**OUT :** `short_render.mp4`

**Tests de production :**
- 2026-05-22 — EN COURS : roadmap.json disponible (F02 scellée), transfert F03/IN à compléter avant lancement

---

## F04 — HELBRECHT

**Composants :**
- `CRS_F04.ipynb` — Notebook Colab (point d'entrée opérateur)
- `crs_f04_helbrecht.py` — FFmpeg remux, injection métadonnées, probe vidéo
- `README_DEV.md` — Documentation développeur

**IN :** `short_render.mp4`, `timing.json`
**OUT :** `final_master.mp4`

**Tests de production :**
- En attente de short_render.mp4 (sortie F03)

---

## METAPROMPTS

**Composants :**
- `META_01_SCRIPT.md` — Génération de script viral via Claude (analyse patterns + balisage [mots_forts])
- `META_02_VISUELS.md` — Génération de visuels via Gemini 3.1 Pro (MODE GROUPED ou 1:1)

**Flux :**
```
Opérateur → META_01 (Claude) → script.txt
Opérateur → META_02 (Gemini) → 1.png, 2.png... → SHARED/images/
```

**Statut :** SCELLÉS — prêts à l'emploi en production
