# F01 GRIMALDUS — README DEV
## Transcription Audio → timing.json

---

## Rôle

GRIMALDUS prend le fichier audio brut et le transcrit mot par mot via **faster-whisper** (local, GPU Colab T4, gratuit). Il produit `timing.json` — le document de référence temporelle pour tout le reste du pipeline.

---

## Stack

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.10+ | Runtime |
| faster-whisper | >= 1.0.0 | Transcription + word timestamps |
| CUDA | T4 (Colab) | Accélération GPU |

---

## Inputs / Outputs

```
F01_GRIMALDUS/
├── IN/
│   └── audio_clean.mp3       ← Fichier audio finalisé (voix seule)
├── OUT/
│   └── timing.json           ← Contrat de données pour F02, F03, F04
└── CODEBASE/
    ├── CRS_F01.ipynb
    ├── crs_f01_grimaldus.py
    └── README_DEV.md
```

---

## Schéma timing.json

```json
{
  "meta": {
    "fps": 30,
    "duration_seconds": 8.6,
    "total_frames": 258,
    "audio_path": "/content/drive/.../F01_GRIMALDUS/IN/audio_clean.mp3",
    "model": "medium",
    "language": "fr",
    "language_probability": 0.9987,
    "word_count": 26,
    "strong_word_count": 3
  },
  "words": [
    {
      "word": "Vous",
      "start": 0.0,
      "end": 0.3,
      "start_frame": 0,
      "end_frame": 9,
      "probability": 0.9921,
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
      "words": [ ... ]
    }
  ]
}
```

---

## Détection des Mots Forts (`is_strong`)

Un mot est marqué `is_strong: true` si l'une des conditions suivantes est vraie :

| Priorité | Condition | Exemple |
|----------|-----------|---------|
| 1 | Balisé `[mot]` par l'opérateur dans le script | `[téléphone]` |
| 2 | En MAJUSCULES dans la transcription | `MAINTENANT` |
| 3 | Durée > 1.8× la durée moyenne des mots | mot allongé stylistiquement |
| 4 | >= 7 caractères ET pas un stopword français | `cerveau`, `dopamine` |

Ces mots seront rendus en police accent (Playfair Display Italic) dans F03.

---

## Modèles disponibles

| Modèle | Précision | Vitesse Colab T4 |
|--------|-----------|------------------|
| `tiny` | Faible | ~5s pour 60s audio |
| `base` | Moyenne | ~10s |
| `small` | Bonne | ~20s |
| `medium` | **Recommandé** | ~40s |
| `large-v3` | Maximale | ~2min |

**Défaut : `medium`** — bon compromis précision/vitesse pour du contenu éducatif français.

---

## Commande d'exécution

```bash
python crs_f01_grimaldus.py \
  --input  /content/drive/MyDrive/DRIVE_CRUSADER/F01_GRIMALDUS/IN/ \
  --output /content/drive/MyDrive/DRIVE_CRUSADER/F01_GRIMALDUS/OUT/ \
  --fps    30 \
  --model  medium
```

---

## Validation CUSTOS

```bash
# Avant de lancer (vérifier que l'audio est en place)
python CRS_CUSTOS.py --frigate F01 --mode check-out

# Après execution (vérifier que timing.json est produit et valide)
python CRS_CUSTOS.py --frigate F01 --mode check-in
```
