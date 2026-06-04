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

## ⚔ VICTORIA AETERNA — PHASE DE TEST

**2026-05-27 — AU NOM DE L'EMPEREUR**

La phase de test est officiellement terminée.
Le pipeline CRUSADER F01 → F04 a été validé en conditions de production réelles.

Chaque frégate a accompli sa mission. La flotte est prête à la croisade.

*"For the Emperor and the Primarchs!"* — High Marshal Helbrecht, Black Templars

---

## ⚔ VICTORIA AETERNA — CAMP_02

**2026-06-04 — AU NOM DE L'EMPEREUR**

La campagne CAMP_02 est officiellement terminée. Pipeline complet exécuté en production réelle :
F01A → F01B → F02 → F03 (GitHub Actions, 10 workers, 4m12s) → F04 → youtube_short.mp4 livré.

Le camouflage de F04 est parfait. La vidéo est propre, sans empreinte d'outil, prête à l'upload YouTube.

Correctif final appliqué post-validation : tag `encoder=Lavf` neutralisé, QA renforcé (`lavf`/`lavc` dans SUSPICIOUS_TAGS).

*"No pity. No remorse. No fear."* — Black Templars

---

## CAMP_02 — TERMINÉE

**2026-05-28 → 2026-06-04 — PRODUCTION RÉELLE**

| Étape | Statut | Résultat |
|-------|--------|---------|
| F01-A CASTELLAN-AUDIO | VALIDÉE | audio_clean.mp3 — 16.7s, 9 silences supprimés |
| F01-B GRIMALDUS | VALIDÉE | timing.json — 531 frames, 46 mots, 5 forts, EN 98.54% |
| F02 CASTELLAN | VALIDÉE | roadmap.json — 531 frames, vertical 1080×1920, validated_by_magos |
| F03 SIGISMUND | VALIDÉE | short_render.mp4 — 531 frames, 17.7s @ 30fps, 16 MB, 10 workers GitHub Actions, 4m12s |
| F04 HELBRECHT | VALIDÉE | youtube_short.mp4 — 14.1 MB, 1080×1920, 17.6s, H264/AAC, camouflage PASS, QA PASS |

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
| 2026-06-04 | Migration Modal → GitHub Actions pour F03 | Modal = CB requise après free tier. GHA = 2000 min/mois gratuit, 10 workers parallèles, zero CB — CAMP_02 validé en 4m12s |
| 2026-06-04 | F04 : `-metadata encoder=` ajouté + `lavf`/`lavc` dans SUSPICIOUS_TAGS | Tag Lavf résiduel neutralisé post-validation CAMP_02 — camouflage désormais 100% |

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
| 2026-05-28 | F03 | CORRECTIF | crs_f03_modal_worker.py — 8 fichiers overlays JSX ajoutés dans _build_remotion_project() (absents → import OverlayDispatch plantait au build Modal) | ✓ |
| 2026-05-28 | F01B | CORRECTIF | CRS_F01.ipynb — URL script corrigée (ancien chemin F01_GRIMALDUS/CODEBASE/ → F01B_GRIMALDUS/CODEBASE/) | ✓ |
| 2026-05-28 | F01A | CORRECTIF | CRS_CUSTOS.py — Support F01A ajouté (check-out: audio_raw.mp3, check-in: audio_clean.mp3) | ✓ |
| 2026-05-28 | F01A | CORRECTIF | CRS_F01A.ipynb — Modes CUSTOS inversés corrigés (check-in ↔ check-out remis dans l'ordre) | ✓ |
| 2026-05-28 | F01A | PROD RÉEL | RÉUSSI — CAMP_02 : audio_raw.mp3 (36.3s) → audio_clean.mp3 (16.7s), 9 silences supprimés (19.58s), CUSTOS OK | ✓ |
| 2026-05-28 | F01B | PROD RÉEL | RÉUSSI — CAMP_02 : timing.json produit : 46 mots, 5 mots forts, 3 segments, 531 frames (17.7s @ 30fps), EN 98.54%, CUSTOS OK | ✓ |
| 2026-06-04 | F03 | MIGRATION | Modal remplacé par GitHub Actions — f03_render.yml (10 workers, gratuit, aucune CB) — crs_f03_gh_trigger.py refactorisé | ✓ |
| 2026-06-04 | F03 | CORRECTIF | CRS_F03.ipynb — suppression final_video_bytes redondant (Step 9 déjà sauvegarde sur Drive, Step 10 converti en vérification) | ✓ |
| 2026-06-04 | F03 | PROD RÉEL | RÉUSSI — CAMP_02 : short_render.mp4 (16 MB, 531 frames, 17.7s @ 30fps), 10 workers GHA, 4m12s, Preflight+10 chunks+Concat SUCCESS | ✓ |
| 2026-06-04 | F04 | PROD RÉEL | RÉUSSI — CAMP_02 : youtube_short.mp4 (14.1 MB, 1080×1920, 17.6s, H264 CRF18 / AAC 48kHz), camouflage PASS, QA pré/post PASS | ✓ |
| 2026-06-04 | F04 | CORRECTIF | `-metadata encoder=` ajouté à la commande FFmpeg — tag Lavf résiduel neutralisé. `lavf`/`lavc` ajoutés dans SUSPICIOUS_TAGS | ✓ |
| 2026-06-04 | PIPELINE | CLÔTURE CAMP_02 | CAMP_02 officiellement terminée — Pipeline F01A→F01B→F02→F03→F04 validé en production réelle. Victoria Aeterna. | ✓ |

---

## F01 — GRIMALDUS
- CRS_F01A.ipynb + crs_f01a.py — Nettoyage audio (suppression silences via Flask)
- CRS_F01.ipynb + crs_f01_grimaldus.py — Transcription faster-whisper, détection mots forts
- IN: audio_raw.mp3 → audio_clean.mp3 → OUT: timing.json
- Test 2026-05-22 (CAMP_01): RÉUSSI — 43 segments, 109.7s
- Prod réelle 2026-05-28 (CAMP_02): RÉUSSI — 46 mots, 5 forts, 3 seg, 531 frames, 17.7s, EN 98.54%

## F02 — CASTELLAN
- CRS_F02.ipynb, crs_f02_castellan.py, crs_f02_viewer.html, README_DEV.md
- IN: timing.json, images/ | OUT: roadmap.json
- Test 2026-05-22: RÉUSSI — 43 segments, 1080×1920, 7 images, validated_by_magos: true
- Prod réelle CAMP_02: RÉUSSI — roadmap.json 531 frames, vertical, consommé avec succès par F03

## F03 — SIGISMUND
- CRS_F03.ipynb, crs_f03_sigismund.py, crs_f03_gh_trigger.py, package.json, remotion.config.js, src/ (JSX), f03_render.yml
- IN: timing.json, roadmap.json, audio_clean.mp3, images/ | OUT: short_render.mp4
- Test 2026-05-26 (CAMP_01 — Modal): RÉUSSI — 3280 frames, 3 workers, 45.4 MB final
- Prod réelle 2026-06-04 (CAMP_02 — GitHub Actions): RÉUSSI — 531 frames, 10 workers, 16 MB, 4m12s
- Anomalies non bloquantes v2: flashs blancs aux transitions, Ken Burns peu perceptible

## F04 — HELBRECHT
- CRS_F04.ipynb, crs_f04_helbrecht.py, README_DEV.md
- IN: short_render.mp4, timing.json | OUT: youtube_short.mp4 ou youtube_long.mp4
- Test 2026-05-27 (CAMP_01): RÉUSSI — youtube_short.mp4 (36.9 MB, 1080×1920, 109.5s), H264/AAC, camouflage total, QA PASS
- Prod réelle 2026-06-04 (CAMP_02): RÉUSSI — youtube_short.mp4 (14.1 MB, 1080×1920, 17.6s), camouflage PASS, QA PASS
- Correctif post-CAMP_02: tag encoder Lavf neutralisé (`-metadata encoder=`), SUSPICIOUS_TAGS renforcé

## METAPROMPTS
- META_01_SCRIPT.md — Script viral via Claude
- META_02_VISUELS.md — Visuels Gemini 3.1 Pro
- Statut: SCELLÉS — prêts à l'emploi
