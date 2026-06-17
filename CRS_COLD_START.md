# CRUSADER — COLD START (Rubicon Primaris)

## 1. Système

```bash
apt-get install -y ffmpeg python3-pip
pip install flask pydub faster-whisper requests
```

## 2. Clone

```bash
git clone https://github.com/kioka8877-ux/CRUSADER.git
cd CRUSADER
```

## 3. Variables

```bash
export GH_TOKEN=<token GitHub scope:repo>
```

## 4. Déposer les assets opérateur

Avant de lancer, l'opérateur dépose dans `SHARED/IN/` :
- `audio_raw.mp3` — voix off brute
- `images/` — dossier avec les visuels de la vidéo

## 5. Lancer

### Nouvelle production
```bash
python CRS_EXECUTEUR.py --start --title "Mon sujet"
```

### Reprendre une production en cours (sandbox mort)
```bash
python CRS_EXECUTEUR.py --resume
```

### Avancer après validation opérateur
```bash
# Après avoir validé le viewer F02 (http://localhost:5002)
python CRS_EXECUTEUR.py --gate G2

# Après avoir validé short_render.mp4
python CRS_EXECUTEUR.py --gate G3

# Après avoir uploadé youtube_final.mp4 sur YouTube
python CRS_EXECUTEUR.py --gate G4
```

## 6. Les 4 portes

| Porte | Ce que fait Claude | Ce que fait l'opérateur |
|-------|--------------------|------------------------|
| G1 | F01A (silences) → F01B (transcription) → Lance F02 viewer | Valider roadmap.json sur http://localhost:5002 |
| G2 | F03 GitHub Actions (upload + trigger + poll + download) | Valider short_render.mp4 |
| G3 | F04 (assemblage final FFmpeg) | Valider youtube_final.mp4 + upload YouTube |
| G4 | Archiver ledger, clôturer | — |

## 7. Reprise après crash

Le ledger `crs_ledger.json` est pushé sur GitHub après chaque gate.
En nouveau sandbox :

```bash
git clone https://github.com/kioka8877-ux/CRUSADER.git
cd CRUSADER
export GH_TOKEN=<token>
python CRS_EXECUTEUR.py --resume
```

Claude Exécuteur reprend exactement là où le sandbox précédent s'est arrêté.
