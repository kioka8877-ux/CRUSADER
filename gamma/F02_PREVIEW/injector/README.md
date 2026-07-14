# CRUSADER — Roadmap Injector v1

## Concept

L'injecteur est un **gardien du contrat** qui vit dans F02_PREVIEW/injector/.
Il ne modifie **jamais** le code F02. Il valide et corrige un roadmap.json exporté
pour qu'il respecte le contrat announce-sync.

## Pourquoi

F02 exporte un roadmap.json avec les crops/waypoints manuels de l'opérateur,
mais **sans** les announce frames (l'UI F02 n'a pas encore ces champs).
L'injecteur comble ce gap en injectant les frames depuis timing.json.

## Architecture

```
F02 export → roadmap.json (crops manuels, sans announce frames)
                    ↓
            Oracle valide via inject.py
                    ↓
           ┌── Correct ? ───┐
           │                 │
         OUI               NON
           │                 │
      Pass through     Injecteur s'active
                             │
                   Lit timing.json
                   Trouve les announce frames
                   Injecte: announce_start/end_frame
                            label, start_segment
                   Préserve: crops, waypoints, fragments
                             │
                   roadmap.json corrigé
                             │
                   → F03 render
```

## Usage

```bash
# Validation seule (dry-run)
python inject.py --roadmap roadmap.json --timing timing.json --dry-run

# Correction + écriture
python inject.py --roadmap roadmap.json --timing timing.json --output corrected.json

# Correction en place
python inject.py --roadmap roadmap.json --timing timing.json
```

## Règles (rules.json)

| Règle | Condition | Action | Sévérité |
|-------|-----------|--------|----------|
| announce_frames | Si null | Détecter dans timing.json | critical |
| chapter_labels | Si "Chapitre N" | Remplacer par vrai nom | critical |
| start_segment | Si incorrect | Remapper | warning |
| text_subtitles | Si absent | Injecter depuis timing.json | critical |
| timeline_count | Si != timing segments | Alerte | warning |
| chapter_count | Si != annonces script | Alerte | warning |
| preserve_manual | Toujours | NE JAMAIS toucher crops/waypoints/fragments | critical |

## Ce que l'injecteur NE fait PAS

- ❌ Modifie les crops/waypoints/fragments (travail manuel)
- ❌ Change le style
- ❌ Touche à la timeline
- ❌ Interagit avec l'UI F02

## Détection des annonces

L'injecteur scanne timing.json pour trouver les segments qui annoncent
le nom d'un chapitre (ex: "Category 1 hurricane.", "Cyclone", "Hypercane").

Stratégie:
1. Match exact: segment = juste le nom
2. Match prefix: segment commence par le nom
3. Word-level: utilise les frames des mots Whisper pour affiner

## Noms de chapitres connus (script tornado)

1. Tropical storm
2. Category 1 hurricane
3. Category 3 hurricane
4. Category 5
5. Super typhoon
6. Cyclone
7. Bomb Cyclone
8. Hypercane
