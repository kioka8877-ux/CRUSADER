# CRUSADER — COLD START v3 (GitHub Actions Edition)

Sandbox = télécommande uniquement. Toutes les frégates tournent sur GitHub Actions.
Zéro compute local. 4 gates opérateur.

---

## 1. Setup (nouveau sandbox)

```bash
git clone https://ghp_TOKEN@github.com/kioka8877-ux/CRUSADER.git /tmp/CRUSADER
export GH_TOKEN=ghp_TOKEN
cd /tmp/CRUSADER
```

Zéro installation manuelle. `requests` s'installe automatiquement si absent.

---

## 2. Assets SHARED/IN/

Les assets de production sont commitées dans le repo — plus besoin de re-uploader.

```
SHARED/IN/
  audio_raw.mp3          ← voix off brute
  images/
    00_00_270.png         ← images nommées par timestamp
    00_09_210.png
    ...
```

Pour une nouvelle production : remplacer les fichiers et commiter avant `--start`.

---

## 3. Commandes orchestrateur

```bash
# Nouvelle production
python CRS_EXECUTEUR.py --start --title "Mon Sujet"
# → upload assets sur GH Release → trigger F01 → print URL → exit

# Gate G2 (F01 terminé sur GH)
python CRS_EXECUTEUR.py --gate G2
# → download timing.json + audio_clean → serve viewer port 8080 → exit quand roadmap sauvegardée

# Gate G3 (roadmap validée)
python CRS_EXECUTEUR.py --gate G3
# → upload roadmap → trigger F03 → print URL → exit

# Gate G4 (F03 terminé sur GH)
python CRS_EXECUTEUR.py --gate G4
# → download short_render → trigger F04 → print URL → exit

# Close (F04 terminé sur GH)
python CRS_EXECUTEUR.py --close
# → download youtube_final + clean_final → archiver ledger → Victoria Aeterna

# Reprendre après crash
python CRS_EXECUTEUR.py --resume
# → lit le ledger, reprend à la gate en cours
```

---

## 4. Les 4 gates opérateur

| Gate | Claude (sandbox) | GitHub Actions | Opérateur |
|------|-----------------|----------------|-----------|
| G1 | Upload + trigger F01 + print URL | F01A (silences) + F01B (Whisper) | Vérifier transcription ✓ |
| G2 | Serve viewer F02 port 8080 | — | Valider roadmap.json dans le viewer ✓ |
| G3 | Upload roadmap + trigger F03 + print URL | F03 Remotion Docker 10 workers | Vérifier short_render.mp4 ✓ |
| G4 | Download F03 + trigger F04 + print URL | F04 assemblage + F05 LUTHER auto | Valider youtube_final.mp4 ✓ |

---

## 5. Workflows GitHub Actions

| Workflow | Fichier | Runner | Durée approx. |
|----------|---------|--------|---------------|
| F01 Audio + Whisper | `f01_grimaldus.yml` | ubuntu-latest | ~5 min |
| F03 Remotion Render | `f03_render.yml` | Docker `crusader-remotion:latest` (10 workers) | ~16 min |
| F04 + F05 Assemblage + Luther | `f04_helbrecht.yml` | ubuntu-latest | ~3 min |
| Docker build image | `docker-build.yml` | ubuntu-latest | ~12 min (une seule fois) |

Secret GitHub requis : `GH_TOKEN` (scope `repo` + `workflow`) dans Settings → Secrets.

---

## 6. F02 Viewer — port 8080

Le viewer se lance automatiquement via `--gate G2`. Il expose le port 8080.
Exposer le port : `/app/export-port.sh 8080` → URL publique.

Fonctionnalités :
- Mapping image → segment audio (avec timing audio en lecture)
- Champ type média par segment : image | video | gif
- Champ SFX override par segment (optionnel)
- Format : horizontal 1920×1080 par défaut (param URL `?format=vertical` si besoin)
- Mapping pré-calculé chargeable en un clic
- POST /api/save → sauvegarde roadmap.json → serveur s'arrête automatiquement

---

## 7. F05 LUTHER — automatique

LUTHER se déclenche automatiquement après F04 (job GitHub Actions, `needs: helbrecht`).
Pas de gate supplémentaire. Deux artifacts disponibles à la fin :
- `youtube-final` → avec titre et date (F04)
- `clean-final` → empreinte zéro, métadonnées effacées (F05)

---

## 8. Reprendre après un crash mid-session

Le ledger `crs_ledger.json` contient l'état exact de la production en cours.

```bash
cat crs_ledger.json  # voir run_id, gate actuelle, GH run IDs
python CRS_EXECUTEUR.py --resume
```

Si la production était à G3 ou G4, les artefacts sont sur la GH Release — pas besoin de tout relancer.

---

## 9. Leçons G1 — Process F01A (silence removal)

**F01A = JAMAIS automatique.** L'opérateur décide quels silences supprimer.

Process correct :
```bash
# 1. Lancer le serveur F01A en background
cd gamma/F01_GRIMALDUS/F01A_CASTELLAN_AUDIO
python CODEBASE/crs_f01a.py --input IN --output OUT --port 5001 &

# 2. Générer le viewer standalone (HTML exportable à l'opérateur)
python CODEBASE/generate_standalone_viewer.py --port 5001 --audio IN/audio_raw.mp3 --output viewer_standalone.html

# 3. Exporter viewer_standalone.html à l'opérateur
# 4. Opérateur écoute, coche/décoche silences, clique VALIDATE, copie le JSON
# 5. Agent génère audio_clean.mp3 en local (FFmpeg trim+concat)
# 6. Push audio_clean.mp3 dans F01A/OUT/
# 7. Trigger F01B sur GitHub Actions avec skip_f01a=true
```

**Permissions GitHub Actions :** tout workflow qui push doit avoir `permissions: contents: write` dans le job.

**F01B = GitHub Actions uniquement.** Ne jamais tenter Whisper en local dans le sandbox.

---

## 10. Spec visuelle BETA (Remotion F03)

Voir `TRACKING/CRUSADER_CAMPAIGN_LOG.md` section CAMP_03 pour la spec complète.

Résumé :
- Monde 2D, caméra voyage de N vers N+1 (zigzag top-right / bottom-right)
- Ressort : mass 0.4 / stiffness 210 / damping 14 / 10 frames
- SFX : index < 3 → à chaque apparition / index ≥ 3 → toutes les 3 apparitions
- Médias supportés : image, video clip, gif


---

## DELTA-TEST3 — Test Production (2026-07-15) ✅

### Résultat : SUCCÈS

Pipeline complet CRUSADER validé de bout en bout sur la branche `delta-test3`.

| Frégate | Statut | Détails |
|---------|--------|---------|
| F00 ASSET FORGE | ✅ Pré-généré | 93 visuels (frame_*.png, gif_*.gif, custom_*.png) |
| F01 GRIMALDUS | ✅ SUCCESS | Audio + transcription — 82 segments, 793 mots, 267.67s |
| F02 CASTELLAN/PREVIEW | ✅ SUCCESS | Preview + UI curation interactive + injecteur de visuels |
| F03 SIGISMUND | ✅ SUCCESS | Render Remotion CrusaderDelta — 8030 frames, 10/10 chunks OK |
| F04 HELBRECHT | ✅ SUCCESS | Camouflage + finalisation YouTube |
| F05 LUTHER | ✅ SUCCESS | Publication |

### Composition utilisée

`CrusaderDelta` — la composition complète avec :
- **Capsules WorldScene sinusoïdal** (82 segments, caméra voyage le long d'une courbe)
- **8 miniatures announce-sync** (overlay pendant l'annonce du nom de chaque chapitre)
- **Sous-titres mot par mot** synchronisés avec timing.json
- **Fond papier + grain + vignette** (Background.jsx)

### Fixes appliqués pendant le test

1. **`public/images/` subdirectory** — Scene.jsx utilise `staticFile("images/...")` mais les images sont dans `public/` directement. Fix : créer `public/images/` et copier les fichiers au runtime dans le workflow.
2. **Composition `CrusaderDelta`** — le workflow utilisait `CrusaderShort` par défaut (Main.jsx = Background + Scene + Subtitle seulement). `CrusaderDelta` ajoute les capsules WorldScene + miniatures announce.
3. **UI curation thumbnails** — 82 micro-previews (80×45px JPEG) embarquées dans l'HTML pour visualiser tous les visuels.
4. **Auto-sync base64** — l'export de curation inclut les images uploadées en base64 → zéro aller-retour.

### Vidéo finale

- **Durée** : 4:27 (8030 frames @ 30fps)
- **Résolution** : 1920×1080
- **Taille** : 101.6 MB
- **Google Drive** : https://drive.google.com/file/d/1Lx-e7I4aS32Y7aFZSjm-hP-LHtakr2Q_/view

### GitHub Actions runs

- F03 full render : https://github.com/kioka8877-ux/CRUSADER/actions/runs/29413597705
- F03 600f test : https://github.com/kioka8877-ux/CRUSADER/actions/runs/29412600871
- F04 finalisation : https://github.com/kioka8877-ux/CRUSADER/actions/runs/29426866194

### Conclusion

Le pipeline CRUSADER gamma est **validé pour la production**. Tous les modules F00→F05 fonctionnent correctement. La composition `CrusaderDelta` produit une vidéo avec capsules, miniatures announce, sous-titres et visuels personnalisables via l'injecteur.
