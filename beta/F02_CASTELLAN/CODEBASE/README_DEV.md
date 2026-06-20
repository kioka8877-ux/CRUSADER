# F02 CASTELLAN — README DEV
## Config Créative + Viewer → roadmap.json

---

## Rôle

CASTELLAN prend `timing.json` (produit par F01) et le dossier `images/`, et expose
un **serveur Flask + interface HTML interactive** à l'opérateur.
L'opérateur assigne une image à chaque segment, configure le style visuel, valide,
et produit `roadmap.json` — le contrat de données pour F03 (rendu Remotion).

---

## Stack

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.10+ | Runtime |
| Flask | >= 2.0 | Serveur REST + fichiers statiques |
| HTML/JS | Natif | Viewer interactif (aucune dépendance JS externe) |
| GPU | Non requis | CPU suffit |

---

## Inputs / Outputs

```
F02_CASTELLAN/
├── IN/
│   ├── timing.json           ← Produit par F01 GRIMALDUS
│   └── images/               ← Images stickman (1.png, 2.png, ...)
├── OUT/
│   └── roadmap.json          ← Contrat de données pour F03 SIGISMUND
└── CODEBASE/
    ├── CRS_F02.ipynb
    ├── crs_f02_castellan.py
    ├── crs_f02_viewer.html
    └── README_DEV.md
```

---

## Schéma roadmap.json

```json
{
  "meta": {
    "fps": 30,
    "format": "vertical",
    "width": 1080,
    "height": 1920,
    "audio_path": "/content/drive/.../IN/audio_clean.mp3",
    "source_timing": "timing.json"
  },
  "style": {
    "font_primary": "Cinzel",
    "font_accent": "Playfair Display",
    "subtitle_size": 72,
    "subtitle_position": "bottom",
    "subtitle_color": "#FFFFFF",
    "accent_color": "#FFD700",
    "background_color": "#F5F0E8",
    "grain_intensity": 0.15,
    "vignette": true
  },
  "timeline": [
    {
      "id": 1,
      "image_file": "1.png",
      "text_subtitles": "Vous pensez trop ?",
      "start_frame": 0,
      "end_frame": 90,
      "start": 0.0,
      "end": 3.0
    }
  ],
  "validated_by_magos": true
}
```

---

## Architecture Flask

| Route | Méthode | Description |
|-------|---------|-------------|
| `/` | GET | Sert `crs_f02_viewer.html` |
| `/api/timing` | GET | Retourne le contenu de `timing.json` |
| `/api/images` | GET | Liste les fichiers dans `IN/images/` |
| `/api/image/<filename>` | GET | Sert une image depuis `IN/images/` |
| `/api/save` | POST | Valide et écrit `roadmap.json` dans `OUT/` |
| `/api/status` | GET | État des fichiers IN/OUT |

---

## Viewer HTML — Fonctionnalités

- **Timeline** : un rang par segment, avec texte, plage de frames, et mots forts surlignés
- **Sélecteur d'image** : dropdown par segment + aperçu miniature
- **Auto-assign** : distribue les images proportionnellement sur les segments
- **Panel de style** : format (vertical/horizontal), polices, couleurs, taille sous-titres, grain, vignetage
- **Validation** : bouton VALIDER → POST `/api/save` → feedback visuel

---

## Commande d'exécution (hors Colab)

```bash
python crs_f02_castellan.py \
  --input  /path/to/F02_CASTELLAN/IN/ \
  --output /path/to/F02_CASTELLAN/OUT/ \
  --viewer /path/to/crs_f02_viewer.html \
  --port   5002
```

---

## Validation CUSTOS

```bash
# Avant de lancer (vérifier timing.json + images/ en place)
python CRS_CUSTOS.py --frigate F02 --mode check-out

# Après validation dans le viewer (vérifier roadmap.json produit)
python CRS_CUSTOS.py --frigate F02 --mode check-in
```

---

## Notes de production

- Flask tourne sur `0.0.0.0` — en Colab, l'URL publique est obtenue via `eval_js('google.colab.kernel.proxyPort(5002)')`.
- Le viewer est purement HTML/CSS/JS natif — aucune dépendance externe (pas de React, pas de CDN).
- `validated_by_magos: true` est positionné par le viewer au moment de la sauvegarde — jamais manuellement.
- Si aucune image n'est assignée à un segment, `image_file` vaut `null` — F03 utilisera la couleur de fond.
