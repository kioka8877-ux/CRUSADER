# CRUSADER — COLD START v2 (GitHub Actions Edition)

Sandbox = télécommande uniquement. Toutes les frégates tournent sur GitHub Actions.
Zéro compute local. 4 gates opérateur.

---

## 1. Setup (nouveau sandbox)

```bash
git clone https://ghp_TOKEN@github.com/kioka8877-ux/CRUSADER.git
cd CRUSADER
export GH_TOKEN=ghp_TOKEN
```

Aucune installation manuelle requise. `requests` s'installe automatiquement.

---

## 2. Assets requis dans SHARED/IN/

```
SHARED/IN/
  audio_raw.mp3          ← voix off brute (déjà commitée si production en cours)
  images/
    00_00_270.png         ← images nommées par timestamp
    00_09_210.png
    ...
```

---

## 3. Commandes

### Nouvelle production

```bash
python CRS_EXECUTEUR.py --start --title "Mon Sujet"
```

Upload les assets → déclenche F01 sur GH Actions → affiche le lien → quitte.

**Gate 1 — Opérateur :** ouvrir le lien GH Actions, vérifier que F01 est terminé (transcription OK).

---

### Gate G2 — Viewer F02

```bash
python CRS_EXECUTEUR.py --gate G2
```

Télécharge artefacts F01 → lance viewer F02 sur port 8080 → affiche l'URL.

**Gate 2 — Opérateur :** ouvrir l'URL, configurer et valider roadmap.json dans le viewer.

---

### Gate G3 — F03 Remotion

```bash
python CRS_EXECUTEUR.py --gate G3
```

Upload roadmap.json → déclenche F03 (10 workers) sur GH Actions → affiche le lien → quitte.

**Gate 3 — Opérateur :** ouvrir le lien GH Actions, vérifier short_render.mp4.

---

### Gate G4 — F04 Helbrecht

```bash
python CRS_EXECUTEUR.py --gate G4
```

Télécharge short_render.mp4 → déclenche F04 sur GH Actions → affiche le lien → quitte.

**Gate 4 — Opérateur :** ouvrir le lien GH Actions, valider youtube_final.mp4.

---

### Close — Récupérer l'artefact final

```bash
python CRS_EXECUTEUR.py --close
```

Télécharge youtube_final.mp4 depuis l'artifact F04. Victoria Aeterna.

---

### Reprendre après crash

```bash
python CRS_EXECUTEUR.py --resume
```

Lit le ledger, reprend à la gate en cours.

---

## 4. Les 4 gates

| Gate | Claude (sandbox) | GitHub Actions | Opérateur |
|------|-----------------|----------------|-----------|
| G1 | Upload assets + trigger F01 + print URL | F01A (silences) + F01B (Whisper) | Vérifier transcription |
| G2 | Serve viewer F02 port 8080 | — | Valider roadmap.json |
| G3 | Upload roadmap + trigger F03 + print URL | F03 Remotion 10 workers | Vérifier short_render.mp4 |
| G4 | Download F03 + trigger F04 + print URL | F04 assemblage final | Valider youtube_final.mp4 |

---

## 5. Workflows GitHub Actions

| Workflow | Fichier | Runner | Durée |
|----------|---------|--------|-------|
| F01 Audio + Whisper | `f01_grimaldus.yml` | ubuntu-latest | ~5 min |
| F03 Remotion Render | `f03_render.yml` | Docker custom (10 workers) | ~15 min |
| F04 Assemblage Final | `f04_helbrecht.yml` | ubuntu-latest | ~3 min |

Secret GitHub requis : `GH_TOKEN` (scope `repo`) dans Settings → Secrets.
