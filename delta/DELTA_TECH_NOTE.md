# CRUSADER/delta-test3 — Note technique de handoff

## Contexte
- Repo : `kioka8877-ux/CRUSADER` (branche à créer : `delta-test3` depuis `main`)
- Token GH : *(fourni séparément par l'opérateur — ne pas committer)*
- Gamma est en production et NE DOIT PAS être modifié.
- Delta est une variation de gamma pour des **vidéos à chapitres** (un sujet → N sous-catégories).

---

## Concept vidéo delta
Une miniature PNG avec des icônes numérotées (ex: 7 types de tornades) sert de fil conducteur.

Flux de la vidéo finale :
```
[Miniature apparaît → caméra zoome vers icône 1]
[Narration chapitre 1 — identique gamma : photos + sous-titres Whisper]
[Miniature réapparaît → caméra glisse icône 1 → icône 2]
[Narration chapitre 2]
...
[Narration chapitre N]
```

---

## Architecture technique retenue

### Rendu hybride (inspiré de CYPHER/hybrid-snowfall)
Deux types de séquences Remotion assemblées par FFmpeg dans l'ordre :
- **Séquences miniature** : pan/zoom 2D sur le PNG de la miniature, caméra suit des waypoints
- **Séquences narration** : identiques à gamma F03 SIGISMUND, zéro changement

### Frégates concernées
| Frégate | Modification |
|---------|-------------|
| F01A | Aucune |
| F01B | Aucune — timing.json Whisper pilote tout |
| **F02 CASTELLAN** | Ajout d'un onglet "MINIATURE" dans le viewer existant |
| **F03 SIGISMUND** | Nouveau composant `ThumbnailSequence.jsx` + logique hybride dans `Root.jsx` |
| F04 HELBRECHT | Aucune |
| F05 LUTHER | Aucune |

---

## F02 — Modification du viewer

**Principe** : ajouter un switcher d'onglets en haut du viewer.
- Onglet ROADMAP → interface existante intacte
- Onglet MINIATURE → nouveau panel

**Panel MINIATURE (gauche 300px) :**
- Upload du PNG miniature
- Liste des chapitres (dérivés des segments timing.json — l'opérateur marque quels segments = début de chapitre)
- Champ label par chapitre
- Slider `transition_frames` (durée du mouvement caméra entre icônes)

**Canvas (droite) :**
- Affiche le PNG miniature
- Clic → place une balise numérotée `{id, x, y}` en coordonnées normalisées 0-1
- Preview animé : un point parcourt les balises dans l'ordre (spring CSS) pour visualiser le comportement caméra
- Balises réordonnable / supprimable

**Output** : un seul fichier `roadmap.json` avec deux blocs :
```json
{
  "meta": { "fps": 30, ... },
  "style": { ... },
  "timeline": [ ... ],
  "thumbnail_plan": {
    "file": "thumbnail.png",
    "transition_frames": 45,
    "chapters": [
      { "id": 1, "label": "Rope",     "start_segment": 0,  "waypoint": {"x": 0.18, "y": 0.72} },
      { "id": 2, "label": "Cone",     "start_segment": 8,  "waypoint": {"x": 0.35, "y": 0.45} },
      { "id": 3, "label": "Elephant", "start_segment": 18, "waypoint": {"x": 0.52, "y": 0.30} }
    ]
  }
}
```
`start_segment` = index dans `timing.json → segments[]` (fourni par Whisper).

---

## F03 — Modification Remotion

### Nouveau composant : `ThumbnailSequence.jsx`
Rendu d'une séquence miniature entre deux chapitres.

Inputs :
- `thumbnailSrc` : chemin vers le PNG
- `fromWaypoint` : `{x, y}` normalisé (null si ouverture)
- `toWaypoint` : `{x, y}` normalisé
- `durationInFrames`

Comportement :
- Le PNG remplit le frame (objectFit cover ou contain selon format)
- `transform: scale + translateX/Y` animé par `spring()` de Remotion
- La caméra "virtuelle" part de `fromWaypoint`, zoome et arrive sur `toWaypoint`
- Zoom cible : scale ~2.5 sur l'icône destination

### Modification `Root.jsx`
`calculateMetadata` lit `roadmap.json`. Si `thumbnail_plan` est présent, il reconstruit la timeline hybride :

```
Pour chaque chapitre i :
  1. ThumbnailSequence (from waypoint[i-1] → to waypoint[i])
  2. Séquences narration du chapitre i (Main existant, délégué à un sous-composant)
```

### Modification `Main.jsx`
Extraire la logique de rendu des segments narration dans un composant `NarrationChapter.jsx` qui accepte un subset de `roadmap.timeline` — permet à Root de l'instancier une fois par chapitre.

---

## Contrat de données complet

### timing.json (inchangé — produit par F01B Whisper)
```json
{
  "meta": { "fps": 30, "duration": 328.93, ... },
  "segments": [ { "id": 0, "text": "...", "start": 0.0, "end": 3.2, "words": [...] } ]
}
```

### roadmap.json (delta — F02 produit, F03 consomme)
```json
{
  "meta": { "fps": 30, "format": "vertical", "width": 1080, "height": 1920, "audio_path": "audio_clean.mp3" },
  "style": { "font_primary": "Cinzel", "subtitle_color": "#FFFFFF", ... },
  "timeline": [ { "id": 0, "image_file": "00_00_270.png", "start_frame": 0, "end_frame": 96, ... } ],
  "thumbnail_plan": {
    "file": "thumbnail.png",
    "transition_frames": 45,
    "chapters": [
      { "id": 1, "label": "Rope",  "start_segment": 0,  "waypoint": {"x": 0.18, "y": 0.72} },
      { "id": 2, "label": "Cone",  "start_segment": 12, "waypoint": {"x": 0.35, "y": 0.45} }
    ]
  },
  "validated_by_magos": true
}
```

---

## Stack technique
- Tout en Remotion ^4.0 + React 18 — zéro nouvelle dépendance
- Waypoints 2D normalisés — Remotion recalcule en pixels réels selon width/height
- Spring animation : `spring({ frame, fps, config: { mass: 0.4, stiffness: 210, damping: 14 } })`
- Rendu GH Actions : même Dockerfile que gamma (crusader-remotion:latest)
- Viewer F02 : HTML/CSS/JS natif, zéro framework, zéro CDN (même convention que gamma)

---

## Prochaines étapes (dans l'ordre)
1. Créer la branche `delta-test3` depuis `main`
2. Modifier `crs_f02_viewer.html` — ajouter onglet MINIATURE + canvas waypoints
3. Créer `ThumbnailSequence.jsx` dans F03/src/components/
4. Modifier `Root.jsx` pour gérer la timeline hybride si `thumbnail_plan` présent
5. Extraire `NarrationChapter.jsx` depuis `Main.jsx`
6. Mettre à jour `CRS_CUSTOS.py` — ajouter `thumbnail_plan` dans le manifeste F02 OUT
7. Tester sur le script tornades

---

## Références
- Viewer F02 actuel : `delta/F02_CASTELLAN/CODEBASE/crs_f02_viewer.html` (64KB)
- F03 Remotion actuel : `delta/F03_SIGISMUND/CODEBASE/src/`
- Inspiration hybride : `kioka8877-ux/CYPHER` branche `hybrid-snowfall` — F03_DEATHWING + F03_GAMMA
- Miniature de référence : image fournie par l'opérateur (7 icônes tornades sur fond blanc, cercles colorés)
