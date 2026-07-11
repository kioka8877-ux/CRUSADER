# CRUSADER — TRANSFER LOG
## Registre des Transferts Inter-Frégates

---

## Procédure Standard de Transit

1. python CRS_CUSTOS.py --frigate <SOURCE> --mode check-out
2. Copier manuellement les fichiers (source OUT/ → destination IN/)
3. python CRS_CUSTOS.py --frigate <DEST> --mode check-in
4. Logger le transfert dans ce fichier

Règle absolue : Aucun transfert sans validation CUSTOS aux deux extrémités.

---

## Schémas JSON — Contrats de Données

### timing.json (produit par F01 GRIMALDUS)
{
  "meta": { "fps": 30, "duration_seconds": 8.6, "total_frames": 258,
            "audio_path": "./assets/audio_clean.mp3", "model": "medium", "language": "fr" },
  "words": [{ "word": "Vous", "start": 0.0, "end": 0.3, "start_frame": 0, "end_frame": 9, "is_strong": false }],
  "segments": [{ "id": 0, "text": "Vous pensez trop ?", "start": 0.0, "end": 1.5, "start_frame": 0, "end_frame": 45, "words": [] }]
}

### roadmap.json (produit par F02 CASTELLAN — alpha)
{
  "meta": { "fps": 30, "format": "vertical", "width": 1080, "height": 1920, "audio_path": "./assets/audio_clean.mp3" },
  "style": { "font_primary": "Cinzel", "font_accent": "Playfair Display", "subtitle_size": 72,
              "subtitle_position": "bottom", "subtitle_color": "#FFFFFF", "accent_color": "#FFD700",
              "grain_intensity": 0.15, "vignette": true, "background_color": "#F5F0E8" },
  "timeline": [{ "id": 1, "image_file": "1.png", "text_subtitles": "Vous pensez trop ?", "start_frame": 0, "end_frame": 90 }],
  "validated_by_magos": true
}

### roadmap.json (produit par F02 CASTELLAN — beta, schéma étendu)
{
  "meta": { "fps": 30, "format": "horizontal", "width": 1920, "height": 1080, "audio_path": "./assets/audio_clean.mp3" },
  "timeline": [{
    "id": 1,
    "image_file": "00_00_270.png",
    "media_type": "image",
    "sfx_trigger": true,
    "trans_frames": 12,
    "text_subtitles": "POV. You are making $50,000 a minute...",
    "start_frame": 0, "end_frame": 90
  }],
  "validated_by_magos": true
}
Champs beta supplémentaires :
  media_type : "image" | "video" | "gif"
  sfx_trigger : true|false — override éditorial du pattern SFX
  trans_frames : 8|12|18|30 — durée de la transition caméra en frames (défaut 12)

### roadmap.json (produit par F02 CASTELLAN — delta-test3, schéma avec thumbnail_plan)
{
  "meta": { "fps": 30, "format": "vertical", "width": 1080, "height": 1920, "audio_path": "./assets/audio_clean.mp3" },
  "style": { "font_primary": "Cinzel", "subtitle_color": "#FFFFFF", "accent_color": "#FFD700", "grain_intensity": 0.15, "vignette": true, "background_color": "#F5F0E8" },
  "timeline": [ { "id": 0, "image_file": "00_00_270.png", "text_subtitles": "...", "start_frame": 0, "end_frame": 96 } ],
  "thumbnail_plan": {
    "file": "thumbnail.png",
    "transition_frames": 45,
    "chapters": [
      { "id": 1, "label": "Rope",     "start_segment": 0,  "waypoint": {"x": 0.18, "y": 0.72} },
      { "id": 2, "label": "Cone",     "start_segment": 12, "waypoint": {"x": 0.35, "y": 0.45} },
      { "id": 3, "label": "Elephant", "start_segment": 24, "waypoint": {"x": 0.52, "y": 0.30} }
    ]
  },
  "validated_by_magos": true
}
Champs delta supplémentaires :
  thumbnail_plan : objet optionnel — si présent, F03 active le mode hybride (séquences miniature + narration)
  thumbnail_plan.file : chemin vers le PNG de la miniature
  thumbnail_plan.transition_frames : durée du mouvement caméra entre icônes (défaut 45)
  thumbnail_plan.chapters[] : liste ordonnée des chapitres
  thumbnail_plan.chapters[].start_segment : index dans timing.json → segments[] (où commence la narration de ce chapitre)
  thumbnail_plan.chapters[].waypoint : coordonnées normalisées 0-1 de l'icône sur le PNG
  thumbnail_plan.chapters[].label : titre du chapitre (affiché dans le viewer)

---

## Matrice des Routes Légales

| Source   | Destination | Fichiers transférés                          |
|----------|-------------|----------------------------------------------|
| SHARED   | F01 IN      | audio_clean.mp3                              |
| SHARED   | F02 IN      | images/, thumbnail.png (delta)               |
| SHARED   | F03 IN      | audio_clean.mp3, images/                     |
| F01 OUT  | F02 IN      | timing.json                                  |
| F01 OUT  | F03 IN      | timing.json                                  |
| F01 OUT  | F04 IN      | timing.json                                  |
| F02 OUT  | F03 IN      | roadmap.json                                 |
| F03 OUT  | F04 IN      | short_render.mp4                             |

---

## Registre des Transferts

| # | Date       | Campagne | Source  | Destination | Fichiers                                        | CUSTOS Out | CUSTOS In | Statut  |
|---|------------|----------|---------|-------------|--------------------------------------------------|------------|-----------|---------|
| 1 | 2026-05-22 | CAMP_01  | F01 OUT | F02 IN      | timing.json (43 seg, 109.7s)                    | OK         | OK        | VALIDÉ  |
| 2 | 2026-05-22 | CAMP_01  | F02 OUT | F03 IN      | roadmap.json (43 seg, vertical, validated)       | OK         | OK        | VALIDÉ  |
| 3 | 2026-05-22 | CAMP_01  | F01 OUT | F03 IN      | timing.json                                      | OK         | OK        | VALIDÉ  |
| 4 | 2026-05-22 | CAMP_01  | SHARED  | F03 IN      | audio_clean.mp3, images/                         | OK         | OK        | VALIDÉ  |
| 5 | 2026-05-26 | CAMP_01  | F03 OUT | F04 IN      | short_render.mp4 (45.4 MB, 109.3s, 3280 frames) | OK         | OK        | VALIDÉ  |
| 6 | 2026-05-27 | CAMP_01  | F04 OUT | OPÉRATEUR   | youtube_short.mp4 (36.9 MB, 109.5s, 1080×1920) | OK         | —         | LIVRÉ   |
| 7 | 2026-05-28 | CAMP_02  | F01A OUT | F01B IN    | audio_clean.mp3 (16.7s, 9 silences supprimés)   | OK         | OK        | VALIDÉ  |
| 8 | 2026-05-28 | CAMP_02  | F01B OUT | F02 IN     | timing.json (46 mots, 5 forts, 531f, 17.7s, EN) | OK         | OK        | VALIDÉ  |
| 9 | 2026-06-04 | CAMP_02  | F02 OUT  | F03 IN     | roadmap.json (531 frames, vertical 1080×1920, validated_by_magos) | OK | OK | VALIDÉ  |
| 10 | 2026-06-04 | CAMP_02 | F01+SHARED | F03 IN  | timing.json + audio_clean.mp3 + images.zip (via GitHub Release automatique) | OK | OK | VALIDÉ  |
| 11 | 2026-06-04 | CAMP_02 | F03 OUT | F04 IN      | short_render.mp4 (16 MB, 531f, 17.7s)          | OK         | OK        | VALIDÉ  |
| 12 | 2026-06-04 | CAMP_02 | F04 OUT | OPÉRATEUR   | youtube_short.mp4 (14.1 MB, 17.6s, 1080×1920, H264/AAC, QA PASS) | OK | — | LIVRÉ |

---

*Tout transfert non loggé ici est considéré non validé.*
