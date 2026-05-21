# META_01 — SCRIPT
## Metaprompt CRUSADER — Génération de Script Viral

> **Outil cible : Claude (claude-sonnet ou claude-opus)**
> Colle ce prompt dans une conversation Claude, en remplissant les variables entre `« »`.

---

## MODE D'EMPLOI

1. Remplis les 5 variables ci-dessous
2. Colle les 3 scripts de référence dans les blocs prévus
3. Envoie le tout à Claude
4. Récupère le script généré → enregistre ta voix off → `audio_clean.mp3`

---

## PROMPT À COPIER-COLLER DANS CLAUDE

```
Tu es un expert en création de contenu viral pour les plateformes courtes (TikTok, YouTube Shorts, Instagram Reels) et longues (YouTube).

---

## MES PARAMÈTRES DE PRODUCTION

- **Sujet** : « SUJET »
- **Durée cible** : « DURÉE » secondes
- **Langue** : « LANGUE »
- **Format** : « FORMAT » (SHORT vertical 9:16 | LONG horizontal 16:9)

---

## MES 3 SCRIPTS DE RÉFÉRENCE VIRAUX

Ces 3 scripts viennent d'une chaîne qui performe bien. Ils représentent le style, la structure et le ton que je veux reproduire.

### Script de référence 1 :
« COLLER LE SCRIPT 1 ICI »

### Script de référence 2 :
« COLLER LE SCRIPT 2 ICI »

### Script de référence 3 :
« COLLER LE SCRIPT 3 ICI »

---

## TA MISSION

**Étape 1 — Analyse des patterns viraux**

Avant de générer quoi que ce soit, analyse les 3 scripts et extrait en silence :
- La structure narrative (accroche, développement, chute/CTA)
- Le rythme des phrases (longueur, cadence, pauses)
- Le style d'accroche (question, affirmation choc, chiffre, paradoxe...)
- Les techniques de rétention utilisées (boucle ouverte, reformulation, escalade)
- Le ton (direct, intime, autoritaire, pédagogue...)
- La densité d'information par seconde

**Étape 2 — Génération du script**

Génère un script sur le sujet demandé en reproduisant exactement ces patterns, adapté au format et à la durée cibles.

**RÈGLES OBLIGATOIRES DE FORMAT :**

1. **Rythme court** : phrases courtes, une idée par phrase. Maximum 12 mots par phrase.
2. **Balisage des mots forts** : encadre les mots-clés importants avec des crochets `[mot]`. Ces mots seront surlignés visuellement dans la vidéo. Maximum 2 mots forts par phrase.
3. **Pauses** : indique les pauses respiratoires avec `...` (3 points).
4. **Structure claire** : sépare chaque phrase/idée sur une nouvelle ligne.
5. **Pas de ponctuation complexe** : pas de guillemets, pas de tirets longs. Virgules et points uniquement.
6. **CTA final** : termine par un appel à l'action naturel (like, commentaire, abonnement) intégré dans le ton du script — jamais en rupture.

**FORMAT DE SORTIE ATTENDU :**

Produis uniquement le script final, sans commentaire ni explication. Structure exacte :

---
[ACCROCHE]
Ligne 1 du script.
Ligne 2 du script avec [mot_fort].
Ligne 3...

[DÉVELOPPEMENT]
Suite du script.
Phrase avec [mot_clé] important.
...

[CHUTE / CTA]
Dernière phrase.
---

Aucun texte avant ou après le script. Uniquement le script formaté.
```

---

## NOTES D'UTILISATION

- **Durée vs nombre de lignes** : environ 2-3 secondes par ligne à débit normal. Pour 60s → 20-25 lignes. Pour 90s → 30-40 lignes.
- **Les `[mots_forts]`** sont directement lus par le pipeline CRUSADER (F02/F03). Ne les modifie pas après génération.
- **Si le script ne convient pas** : dis à Claude "Garde exactement la même structure mais change le ton vers [plus direct / plus pédagogue / plus percutant]".
- **Étape suivante** : enregistre ta voix off en lisant ce script → sauvegarde en `audio_clean.mp3` → dépose dans `DRIVE_CRUSADER/F01_GRIMALDUS/IN/`.
