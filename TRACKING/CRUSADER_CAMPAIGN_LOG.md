# CRUSADER — CAMPAIGN LOG
## Carnet de Bord de Croisade

> *"We are the Emperor's will made manifest."*

---

## Statut de la Flotte

| Frégate | Nom | Rôle | Statut | Date de Scellement |
|---------|-----|------|--------|--------------------|
| F01 | GRIMALDUS | Transcription audio → timing.json | EN FORGE | — |
| F02 | CASTELLAN | Config créative + viewer → roadmap.json | EN FORGE | — |
| F03 | SIGISMUND | Rendu Remotion → short_render.mp4 | EN FORGE | — |
| F04 | HELBRECHT | Assemblage FFmpeg → final_master.mp4 | EN FORGE | — |

**Compteur de Guerre :**
```
[░░░░] 0/4 frégates scellées
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

---

## Fil d'Ariane — Log Chronologique

| Date | Frégate | Phase | Action | Validé |
|------|---------|-------|--------|--------|
| 2026-05-21 | — | INIT | Création du repo CRUSADER sur GitHub | ✓ |
| 2026-05-21 | — | INIT | Structure des frégates initialisée | ✓ |

---

## F01 — GRIMALDUS

**Composants :**
- `CRS_F01.ipynb` — Notebook Colab (point d'entrée opérateur)
- `crs_f01_grimaldus.py` — Script faster-whisper, détection mots forts

**IN :** `audio_clean.mp3`
**OUT :** `timing.json`

**Tests de production :**
*Aucun test effectué — EN FORGE*

---

## F02 — CASTELLAN

**Composants :**
- `CRS_F02.ipynb` — Notebook Colab
- `crs_f02_flask.py` — Serveur Flask REST (port natif Colab)
- `crs_f02_viewer.html` — Interface HTML interactive (mapping, style sous-titres, format)

**IN :** `timing.json`, `images/`
**OUT :** `roadmap.json`

**Tests de production :**
*Aucun test effectué — EN FORGE*

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
