# CRUSADER — CAMPAIGN LOG
## Carnet de Bord de Croisade

> *"We are the Emperor's will made manifest."*

---

## Statut de la Flotte

| Frégate | Nom | Rôle | Statut | Date de Scellement |
|---------|-----|------|--------|--------------------|
| F01 | GRIMALDUS | Transcription audio → timing.json | SCELLÉE — EN TEST PROD | 2026-05-21 |
| F02 | CASTELLAN | Config créative + viewer → roadmap.json | SCELLÉE — EN TEST PROD | 2026-05-21 |
| F03 | SIGISMUND | Rendu Remotion → short_render.mp4 | EN FORGE | — |
| F04 | HELBRECHT | Assemblage FFmpeg → final_master.mp4 | EN FORGE | — |

**Compteur de Guerre :**
```
[██░░] 2/4 frégates scellées
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

---

## Fil d'Ariane — Log Chronologique

| Date | Frégate | Phase | Action | Validé |
|------|---------|-------|--------|--------|
| 2026-05-21 | — | INIT | Création du repo CRUSADER sur GitHub | ✓ |
| 2026-05-21 | — | INIT | Structure des frégates initialisée | ✓ |
| 2026-05-21 | F01 | FORGE | Développement terminé : crs_f01_grimaldus.py + CRS_F01.ipynb | ✓ |
| 2026-05-21 | F01 | TEST PROD | En attente de tests sur audio réel (Colab GPU T4) | — |
| 2026-05-21 | F02 | FORGE | Développement terminé : Flask server + HTML viewer + notebook | ✓ |
| 2026-05-21 | F02 | TEST PROD | En attente de tests avec timing.json + images/ réels | — |

---

## F01 — GRIMALDUS

**Composants :**
- `CRS_F01.ipynb` — Notebook Colab (point d'entrée opérateur)
- `crs_f01_grimaldus.py` — Script faster-whisper, détection mots forts

**IN :** `audio_clean.mp3`
**OUT :** `timing.json`

**Tests de production :**
*Prêt pour test — en attente d'un audio réel sur Colab GPU T4*

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
*Prêt pour test — en attente de timing.json (sortie F01) + images/ réels*

---

## F03 — SIGISMUND

**Composants :**
- `CRS_F03.ipynb` — Notebook Colab
- `src/` — Projet Remotion (React/Node.js)
  - `index.jsx` — Point d'entrée Remotion
  - `Root.jsx` — Composition (durée depuis timing.json)
  - `components/Scene.tsx` — Image + animations (wiggle, pop, pan)
  - `components/Subtitle.tsx` — Sous-titres synchronisés (Cinzel + Playfair)
  - `components/Background.tsx` — Texture papier, grain, vignetage

**IN :** `timing.json`, `roadmap.json`, `audio_clean.mp3`, `images/`
**OUT :** `short_render.mp4`

**Tests de production :**
*Aucun test effectué — EN FORGE*

---

## F04 — HELBRECHT

**Composants :**
- `CRS_F04.ipynb` — Notebook Colab
- `crs_f04_helbrecht.py` — FFmpeg remux, injection métadonnées, viewer vidéo

**IN :** `short_render.mp4`, `timing.json`
**OUT :** `final_master.mp4`

**Tests de production :**
*Aucun test effectué — EN FORGE*
