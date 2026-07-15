# DELTA-TEST3 — Test Production CRUSADER Gamma

**Date** : 2026-07-15  
**Branche** : `delta-test3`  
**Statut** : ✅ **SUCCÈS**  
**Conclusion** : Pipeline validé pour la production

---

## Pipeline validé

| Frégate | Module | Statut | Détails |
|---------|--------|--------|---------|
| F00 | ASSET FORGE | ✅ Pré-généré | 93 visuels (frame_*.png, gif_*.gif, custom_*.png) |
| F01 | GRIMALDUS | ✅ SUCCESS | Audio + transcription — 82 segments, 793 mots, 267.67s |
| F02 | CASTELLAN/PREVIEW | ✅ SUCCESS | Preview + UI curation + injecteur de visuels |
| F03 | SIGISMUND | ✅ SUCCESS | Render Remotion CrusaderDelta — 8030 frames, 10/10 chunks |
| F04 | HELBRECHT | ✅ SUCCESS | Camouflage + finalisation YouTube |
| F05 | LUTHER | ✅ SUCCESS | Publication |

## Composition

`CrusaderDelta` (DeltaMain.jsx) :
- Background (papier + grain + vignette)
- WorldScene (capsules sinusoïdales, 82 segments)
- BetaSubtitle (sous-titres mot par mot synchronisés)
- MiniatureOverlay (8 announce-sync, overlay pendant l'annonce du nom)
- Audio (audio_clean.mp3)

## Vidéo finale

| Champ | Valeur |
|-------|--------|
| Durée | 4:27 (8030 frames @ 30fps) |
| Résolution | 1920×1080 |
| Taille | 101.6 MB |
| Codec | H.264 + AAC 192k |
| Google Drive | https://drive.google.com/file/d/1Lx-e7I4aS32Y7aFZSjm-hP-LHtakr2Q_/view |

## Fixes appliqués pendant le test

1. **`public/images/` subdirectory** — Scene.jsx utilise `staticFile("images/...")` mais les images sont dans `public/` directement. Fix dans `f03_render.yml` : création de `public/images/` et copie des fichiers au runtime.
2. **Composition `CrusaderDelta`** — le workflow utilisait `CrusaderShort` par défaut (Main.jsx = Background + Scene + Subtitle). `CrusaderDelta` ajoute les capsules WorldScene + miniatures announce.
3. **UI curation thumbnails** — 82 micro-previews (80×45px JPEG q40, ~800 bytes chacune) embarquées dans l'HTML.
4. **Auto-sync base64** — `exportCuration()` inclut `upload_data` (base64) pour chaque upload → zéro aller-retour.
5. **Release GitHub** — création manuelle de la release avec timing.json, roadmap.json, audio_clean.mp3, images.zip (62MB) pour alimenter le workflow F03.

## GitHub Actions runs

| Run | Description | Lien |
|-----|-------------|------|
| 29413597705 | F03 full render 8030 frames | https://github.com/kioka8877-ux/CRUSADER/actions/runs/29413597705 |
| 29412600871 | F03 test 600 frames | https://github.com/kioka8877-ux/CRUSADER/actions/runs/29412600871 |
| 29408568523 | F03 test 600 frames (CrusaderShort) | https://github.com/kioka8877-ux/CRUSADER/actions/runs/29408568523 |
| 29426866194 | F04 finalisation | https://github.com/kioka8877-ux/CRUSADER/actions/runs/29426866194 |

## Injecteur de visuels

- 4 visuels remplacés (seg 1, 2, 4, 5) dont 1 GIF animé (25 frames)
- Pipeline : upload UI → export JSON+base64 → décodage → resize 1920×1080 → push GitHub → roadmap update → render
- Zéro aller-retour grâce à l'auto-sync base64

## Conclusion

Le pipeline CRUSADER gamma est **validé pour la production**. Tous les modules F00→F05 fonctionnent correctement. La composition `CrusaderDelta` produit une vidéo professionnelle avec capsules, miniatures announce, sous-titres et visuels personnalisables.
