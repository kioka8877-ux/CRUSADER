# CRUSADER — CAMPAIGN LOG
## Carnet de Bord de Croisade

> *"We are the Emperor's will made manifest."*

---

## Statut de la Flotte

| Frégate | Nom | Rôle | Statut | Date de Scellement |
|---------|-----|------|--------|--------------------|
| F01 | GRIMALDUS | Transcription audio → timing.json | SCELLÉE — TEST PROD RÉUSSI | 2026-05-21 |
| F02 | CASTELLAN | Config créative + viewer → roadmap.json | SCELLÉE — TEST PROD RÉUSSI | 2026-05-21 |
| F03 | SIGISMUND | Rendu Remotion → short_render.mp4 | SCELLÉE — TEST PROD RÉUSSI | 2026-05-26 |
| F04 | HELBRECHT | Assemblage FFmpeg → youtube_short.mp4 | SCELLÉE — TEST PROD RÉUSSI | 2026-05-27 |
| META | METAPROMPTS | Guides opérateur (script + visuels) | SCELLÉS — PRÊTS À L'EMPLOI | 2026-05-21 |

**Compteur de Guerre :**
[████] 4/4 frégates scellées
[██]   2/2 metaprompts scellés
[████] 4/4 tests de production réussis — PIPELINE COMPLET

---

## ⚔ VICTORIA AETERNA

**2026-05-27 — AU NOM DE L'EMPEREUR**

La phase de test est officiellement terminée.
Le pipeline CRUSADER F01 → F04 a été validé en conditions de production réelles.

Chaque frégate a accompli sa mission. La flotte est prête à la croisade.

*"For the Emperor and the Primarchs!"* — High Marshal Helbrecht, Black Templars

---

## Flux de Données

SHARED/audio_clean.mp3 ──► F01 IN, F03 IN
SHARED/images/ ──────────► F02 IN, F03 IN

F01 GRIMALDUS  → timing.json ────────► F02 IN, F03 IN, F04 IN
F02 CASTELLAN  → roadmap.json ───────► F03 IN
F03 SIGISMUND  → short_render.mp4 ───► F04 IN
F04 HELBRECHT  → youtube_short.mp4 ──► Téléchargement opérateur

---

## Rites du Sang — Principes Gouvernants

1. Gratuit — Aucun API payant, aucune dépendance commerciale
2. Colab-first — Tout s'exécute sur Google Colab (GPU T4), le PC est une télécommande
3. 30 fps — Cible fixe, encodée dans le JSON meta
4. Dual format — Vertical 1080×1920 (Shorts) et Horizontal 1920×1080 (Long-form)
5. Isolation des frégates — Chaque frégate opère en silo, lit son IN/, écrit son OUT/
6. Transfert validé — Tout transit inter-frégate passe par CRS_CUSTOS.py (check-out + check-in)

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
| 2026-05-26 | Chunking parallèle Modal (3 workers) | 3280 frames découpées en 3 chunks de ~1093 frames, rendu parallèle |
| 2026-05-27 | F04 v2 : re-encode CRF18 + camouflage | Effacement fingerprints Remotion/OpenCV, loudnorm -14 LUFS, format auto-détecté |

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
| 2026-05-26 | F03 | TEST PROD | RÉUSSI — 3280 frames / 109.3s @ 30fps, 3 workers Modal (Succeeded : 12m09s, 12m22s, 17m14s), short_render.mp4 produit (45.4 MB), validé pour F04 | ✓ |
| 2026-05-27 | F04 | TEST PROD | RÉUSSI — youtube_short.mp4 (36.9 MB, 1080×1920, 1m49s), camouflage PASS, QA pré/post PASS, loudnorm -14 LUFS, faststart activé, aucun tag suspect | ✓ |
| 2026-05-27 | PIPELINE | CLÔTURE TEST | Phase de test officiellement terminée — Pipeline CRUSADER F01→F04 validé. Victoria Aeterna. | ✓ |

---

## F01 — GRIMALDUS
- CRS_F01.ipynb — Notebook Colab
- crs_f01_grimaldus.py — Script faster-whisper, détection mots forts
- IN: audio_clean.mp3 | OUT: timing.json
- Test 2026-05-22: RÉUSSI — 43 segments, 109.7s

## F02 — CASTELLAN
- CRS_F02.ipynb, crs_f02_castellan.py, crs_f02_viewer.html, README_DEV.md
- IN: timing.json, images/ | OUT: roadmap.json
- Test 2026-05-22: RÉUSSI — 43 segments, 1080×1920, 7 images, validated_by_magos: true

## F03 — SIGISMUND
- CRS_F03.ipynb, crs_f03_sigismund.py, package.json, remotion.config.js, src/ (5 JSX files), README_DEV.md
- IN: timing.json, roadmap.json, audio_clean.mp3, images/ | OUT: short_render.mp4
- Test 2026-05-26: RÉUSSI — 3280 frames, 3 Modal chunks (17.8+14.4+13.1 MB), 45.4 MB final
- Anomalies non bloquantes v2: flashs blancs aux transitions, Ken Burns peu perceptible

## F04 — HELBRECHT
- CRS_F04.ipynb, crs_f04_helbrecht.py, README_DEV.md
- IN: short_render.mp4, timing.json | OUT: youtube_short.mp4 ou youtube_long.mp4
- Test 2026-05-27: RÉUSSI — youtube_short.mp4 (36.9 MB, 1080×1920, 109.5s), H264/AAC, camouflage total, QA PASS

## METAPROMPTS
- META_01_SCRIPT.md — Script viral via Claude
- META_02_VISUELS.md — Visuels Gemini 3.1 Pro
- Statut: SCELLÉS — prêts à l'emploi
