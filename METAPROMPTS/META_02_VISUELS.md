# META_02 — VISUELS
## Metaprompt CRUSADER — Génération de Visuels par Gemini 3.1 Pro

> **Outil cible : Gemini 3.1 Pro (capable de lire une vidéo et de générer des images)**
> Colle ce prompt dans Gemini, en joignant la vidéo de référence + les fichiers demandés.

---

## MODE D'EMPLOI

1. Choisis ton **MODE** (GROUPED ou 1:1)
2. Joins la **vidéo de référence** à la conversation Gemini
3. Joints le **script généré** (META_01) et le **timing.json** (F01)
4. Remplis les variables entre `« »`
5. Envoie le tout à Gemini
6. Récupère les images → renomme en `1.png`, `2.png`... → dépose dans `DRIVE_CRUSADER/SHARED/images/`

---

## CHOIX DU MODE

| Mode | Usage | Images générées |
|------|-------|-----------------|
| `GROUPED` | Test / validation pipeline | 1 image par groupe de segments (5-8 images) |
| `1:1` | Production maximale | 1 image par segment (15-30 images) |

---

## PROMPT À COPIER-COLLER DANS GEMINI

```
Tu es un directeur artistique expert en création de contenu vidéo viral (TikTok, YouTube Shorts, Reels).

---

## MES PARAMÈTRES

- **Format de sortie** : « FORMAT » (VERTICAL 9:16 — 1080×1920 | HORIZONTAL 16:9 — 1920×1080)
- **Mode de génération** : « MODE » (GROUPED | 1:1)
- **Style graphique** : extrait de la vidéo de référence que je t'ai fournie

---

## FICHIERS FOURNIS

1. **Vidéo de référence** (jointe) — c'est ton modèle visuel absolu
2. **Script** :
« COLLER LE SCRIPT COMPLET ICI (avec les [mots_forts]) »

3. **timing.json** :
« COLLER LE CONTENU COMPLET DU TIMING.JSON ICI »

---

## ÉTAPE 1 — ANALYSE DE LA VIDÉO DE RÉFÉRENCE

Regarde la vidéo de référence et extrait avec précision :

- **Style graphique** : stickman, whiteboard, esquisse, ligne noire sur fond blanc, etc.
- **Trait** : épais / fin / variable, propre / tremblé / imparfait
- **Palette de couleurs** : fond, personnages, accents
- **Texture** : grain papier, fond uni, texture tableau, vignettage
- **Mise en scène** : cadrage des personnages, proportion corps/décor, densité d'éléments
- **Ambiance générale** : minimaliste, chargée, ludique, sérieuse

---

## ÉTAPE 2 — LECTURE DU TIMING.JSON

Identifie tous les segments (champ `"segments"`) avec leur texte, start et end.

**Si MODE = GROUPED** :
Regroupe les segments qui parlent de la même idée ou scène narrative. Crée des groupes de 3 à 6 segments. Vise 5 à 8 groupes au total.

**Si MODE = 1:1** :
Chaque segment = une image distincte. Ne regroupe rien.

Dans les deux cas, numérote tes groupes/segments de 1 à N.

---

## ÉTAPE 3 — GÉNÉRATION DES VISUELS

Pour chaque groupe (GROUPED) ou segment (1:1), génère une image qui :

1. **Reproduit fidèlement** le style extrait de la vidéo de référence (trait, couleur, texture, ambiance)
2. **Illustre visuellement** ce qui est dit dans le/les segment(s) correspondant(s)
3. **Respecte le format** : « FORMAT » (1080×1920 vertical ou 1920×1080 horizontal)
4. **Reste lisible** : fond clair, contraste fort, pas de texte dans l'image (les sous-titres sont ajoutés par le pipeline)
5. **Style cohérent** : toutes les images doivent avoir exactement le même rendu visuel

---

## ÉTAPE 4 — LIVRAISON

Après avoir généré toutes les images, fournis :

**Tableau de mapping** (format exact — ne pas modifier) :

| Image | Nom fichier | Segments couverts | Texte illustré | Overlay | Intensite |
|-------|-------------|-------------------|----------------|---------|-----------|
| 1 | 1.png | seg 1-3 | "Vous pensez trop ?" | INTERIEUR:neons | 2 |
| 2 | 2.png | seg 4-6 | "C'est à cause de votre [téléphone]." | VITRE:pluie | 2 |
| ... | ... | ... | ... | ... | ... |

Puis génère chaque image dans l'ordre, nommée `1.png`, `2.png`, etc.

---

## RÈGLES ABSOLUES

- Aucun texte dans les images (ni sous-titres, ni titres, ni légendes)
- Aucun filigrane, aucun logo
- Style 100% cohérent entre toutes les images
- Le fond doit correspondre au style de la vidéo de référence
- Les personnages/éléments doivent être dans la même proportion que dans la référence
- **Colonne Overlay** : pour chaque image générée, indique l'overlay le plus adapté au contexte visuel parmi ces valeurs :
  `INTERIEUR:neons` | `INTERIEUR:lampe` | `INTERIEUR:ecran` | `INTERIEUR:sombre` |
  `EXTERIEUR:pluie` | `EXTERIEUR:vent` | `EXTERIEUR:soleil` | `EXTERIEUR:nuit` |
  `VITRE:pluie` | `VITRE:brouillard` | `defaut`
  Utilise `VITRE:xxx` si le personnage est à l'intérieur mais qu'une fenêtre avec météo est visible. Valeur par défaut = `defaut`.
- **Colonne Intensite** : 1 (discret) / 2 (normal) / 3 (dramatique). Utilise 3 uniquement pour les scènes à fort impact émotionnel.
```

---

## APRÈS LA GÉNÉRATION

1. Télécharge toutes les images générées
2. Renomme-les exactement : `1.png`, `2.png`, `3.png`...
3. Dépose-les dans `DRIVE_CRUSADER/SHARED/images/`
4. Copies également dans `DRIVE_CRUSADER/F02_CASTELLAN/IN/images/` et `DRIVE_CRUSADER/F03_SIGISMUND/IN/images/`
5. Tu peux passer à **F02 CASTELLAN**

---

## NOTES

- **Passage de GROUPED à 1:1** : relance simplement le prompt en changeant `MODE = 1:1`. Tout le reste reste identique.
- **Si une image ne correspond pas au style** : dis à Gemini "L'image N ne correspond pas au style de la référence. Régénère-la en accentuant [trait tremblé / fond papier / couleur de fond]."
- **Nombre d'images typique** : GROUPED = 5-8 images / 1:1 = 15-30 images selon la durée de la vidéo.
