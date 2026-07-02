# F02 CASTELLAN — Preview Interactif

## Rôle
Outil de validation visuelle avant le rendu final. Preview Canvas live + éditeur de storyboard.

## Fonctionnalités
- 🔀 Navigation scène par scène (◀ / ▶)
- ▶ Lecture automatique avec auto-advance
- 🧍 Modification posture / émotion / direction en live
- 🎨 Changement de décor (nature, ville, bureau, abstrait)
- ✨ Effets (particules, vignette)
- 💬 Sous-titres éditables avec typing effect
- ➕ Ajout / suppression de scènes
- 📂 Import / 💾 Export storyboard.json
- 🎬 HUD gamma style (titre production, barre progression)

## Usage
Ouvrir `CODEBASE/index.html` dans un navigateur. Le storyboard de test est embarqué.

## Pipeline
```
F02 CASTELLAN (preview) → exporte storyboard.json
    ↓
F03B SCRIPTORIUM (compile) → index_scriptorium.html
    ↓
F03C FONDERIE (render) → frames → MP4
```

## Fichiers
| Fichier | Rôle |
|---------|------|
| `CODEBASE/index.html` | Preview standalone (characters.js + backgrounds.js + effects.js embarqués) |
