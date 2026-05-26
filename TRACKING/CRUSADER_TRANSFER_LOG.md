# CRUSADER — TRANSFER LOG
## Registre des Transferts Inter-Frégates

---

## Procédure Standard de Transit

```
1. python CRS_CUSTOS.py --frigate <SOURCE> --mode check-out
2. Copier manuellement les fichiers (source OUT/ → destination IN/)
3. python CRS_CUSTOS.py --frigate <DEST> --mode check-in
4. Logger le transfert dans ce fichier
```

**Règle absolue :** Aucun transfert sans validation CUSTOS aux deux extrémités.

---

## Schémas JSON — Contrats de Données

### timing.json (produit par F01 GRIMALDUS)
```json
{
  "meta": {
    "fps": 30,
    "duration_seconds": 8.6,
    "total_frames": 258,
    "audio_path": "./assets/audio_clean.mp3",
    "model": "medium",
    "language": "fr"
  },
  "words": [
    {
      "word": "Vous",
      "start": 0.0,
      "end": 0.3,
      "start_frame": 0,
      "end_frame": 9,
      "is_strong": false
    }
  ],
  "segments": [
    {
      "id": 0,
      "text": "Vous pensez trop ?",
      "start": 0.0,
      "end": 1.5,
      "start_frame": 0,
      "end_frame": 45,
      "words": []
    }
  ]
}
```

### roadmap.json (produit par F02 CASTELLAN)
```json
{
  "meta": {
    "fps": 30,
    "format": "vertical",
    "width": 1080,
    "height": 1920,
    "audio_path": "./assets/audio_clean.mp3"
  },
  "style": {
    "font_primary": "Cinzel",
    "font_accent": "Playfair Display",
    "subtitle_size": 72,
    "subtitle_position": "bottom",
    "subtitle_color": "#FFFFFF",
    "accent_color": "#FFD700",
    "grain_intensity": 0.15,
    "vignette": true,
    "background_color": "#F5F0E8"
  },
  "timeline": [
    {
      "id": 1,
      "image_file": "1.png",
      "text_subtitles": "Vous pensez trop ?",
      "start_frame": 0,
      "end_frame": 90
    }
  ],
  "validated_by_magos": true
}
```

---

## Matrice des Routes Légales

| Source | Destination | Fichiers transférés |
|--------|-------------|---------------------|
| SHARED | F01 IN | `audio_clean.mp3` |
| SHARED | F02 IN | `images/` |
| SHARED | F03 IN | `audio_clean.mp3`, `images/` |
| F01 OUT | F02 IN | `timing.json` |
| F01 OUT | F03 IN | `timing.json` |
| F01 OUT | F04 IN | `timing.json` |
| F02 OUT | F03 IN | `roadmap.json` |
| F03 OUT | F04 IN | `short_render.mp4` |

---

## Diagramme des Flux

```
SHARED ──── audio_clean.mp3 ──────────────────────────► F01 IN
       ──── audio_clean.mp3 ──────────────────────────► F03 IN
       ──── images/ ─────────────────────────────────► F02 IN
       ──── images/ ─────────────────────────────────► F03 IN

F01 OUT ─── timing.json ──────────────────────────────► F02 IN
        ─── timing.json ──────────────────────────────► F03 IN
        ─── timing.json ──────────────────────────────► F04 IN

F02 OUT ─── roadmap.json ────────────────────────────► F03 IN

F03 OUT ─── short_render.mp4 ────────────────────────► F04 IN

F04 OUT ─── final_master.mp4 ────────────────────────► Opérateur
```

---

## Registre des Transferts

| # | Date | Campagne | Source | Destination | Fichiers | CUSTOS Out | CUSTOS In | Statut |
|---|------|----------|--------|-------------|----------|-----------|-----------|--------|
| 1 | 2026-05-22 | CAMP_01 | F01 OUT | F02 IN | `timing.json` (43 seg, 109.7s) | OK | OK | VALIDÉ |
| 2 | 2026-05-22 | CAMP_01 | F02 OUT | F03 IN | `roadmap.json` (43 seg, vertical, validated) | OK | OK | VALIDÉ |
| 3 | 2026-05-22 | CAMP_01 | F01 OUT | F03 IN | `timing.json` | OK | OK | VALIDÉ |
| 4 | 2026-05-22 | CAMP_01 | SHARED | F03 IN | `audio_clean.mp3`, `images/` | OK | OK | VALIDÉ |
| 5 | 2026-05-26 | CAMP_01 | F03 OUT | F04 IN | `short_render.mp4` (45.4 MB, 109.3s, 3280 frames) | OK | OK | VALIDÉ |

---

*Tout transfert non loggé ici est considéré non validé.*
