# 🏛️ GUIDE DE L'ORACLE — F00 → F03

> **Comment chercher, ordonner et préparer les assets F00 pour le rendu F03 SIGISMUND.**

---

## 📖 TABLE DES MATIÈRES

1. [La chaîne CRUSADER](#la-chaîne-crusader)
2. [La base d'assets F00](#la-base-dassets-f00)
3. [Recherche d'assets](#recherche-dassets)
4. [Sélection et ordonnancement](#sélection-et-ordonnancement)
5. [Préparation pour F02/F03](#préparation-pour-f02f03)
6. [Exemple complet](#exemple-complet)
7. [Référence des fichiers](#référence-des-fichiers)

---

## LA CHAÎNE CRUSADER

```
F00 ASSET FORGE          F01 GRIMALDUS         F02 CASTELLAN          F03 SIGISMUND
────────────────         ──────────────        ───────────────        ────────────────
Vidéo NASA/NOAA          Voix de référence      Script + timing        Rendu Remotion
  ↓ yt-dlp                 ↓ TTS/Audio           ↓ Gemini mapping       ↓ Chrome headless
  ↓ ffmpeg                 ↓ timing.json         ↓ roadmap.json         ↓ MP4 final
  ↓ OpenRouter Vision      ↓ audio_clean.mp3     ↓ images sélectionnées
  ↓ index.json
  ↓ tag_index.json
```

**L'Oracle intervient entre F00 et F02.** Son rôle :
1. Lire le script à illustrer
2. Chercher les assets pertinents dans la base F00
3. Ordonner les assets pour créer une narration visuelle
4. Produire le `roadmap.json` que F03 consomme

---

## LA BASE D'ASSETS F00

### Fichiers clés

| Fichier | Rôle | Format |
|---------|------|--------|
| `index.json` | Métadonnées de chaque asset | `{ "frame_001": { type, tags, visual_description, usage_tags, ... } }` |
| `tag_index.json` | Reverse-index : tag → assets | `{ "satellite": ["frame_001", "frame_050", ...] }` |
| `oracle_tags_vision.json` | Tags bruts de la vision IA | `{ "frame_001": { visual, narrative, usage } }` |
| `BANK_B_NATURE/fire/` | Frames PNG + GIFs | `frame_000001.png`, `gif_0001.gif` |
| `BANK_D_CLIPS/` | Clips MP4 | `clip_0001.mp4` |
| `CANVAS/` | Grilles de contact (pour vision) | `canvas_frames_nature_fire.png` |

### Structure d'un asset dans index.json

```json
{
  "frame_091": {
    "type": "frame",
    "tags": ["expertise", "interview", "technologie"],
    "visual_description": "Man in suit standing in front of a screen.",
    "usage_tags": ["illustration"],
    "tagged_by": "openrouter-gemma-3-12b",
    "tagged_at": "2026-07-12T01:30:00Z",
    "source": "F00 ASSET FORGE"
  }
}
```

### Tags narratifs disponibles

Les tags sont en français et couvrent ces catégories :

| Catégorie | Tags exemples |
|-----------|---------------|
| **Phénomènes** | tempete, ouragan, inondation, pluie, vent, destruction |
| **Technologie** | satellite, technologie, donnees, mesure, prevision, animation, graphique |
| **Humain** | population, humanite, expertise, interview, danger, alerte |
| **Nature** | nature, globe, eau, carte, terre |
| **Usage** | illustration, transition, background, overlay, intro, outro, b-roll |

---

## RECHERCHE D'ASSETS

### Méthode 1 : Recherche par tags (script Python)

```python
import json

# Charger les index
with open("F00_ASSET_FORGE/tag_index.json") as f:
    tag_index = json.load(f)

with open("F00_ASSET_FORGE/index.json") as f:
    index = json.load(f)

# Chercher "ouragan cat 5"
query_tags = ["ouragan", "tempete", "danger", "destruction"]
results = set()
for tag in query_tags:
    if tag in tag_index:
        results.update(tag_index[tag])

# Trier par nombre de tags matchés
scored = []
for asset_id in results:
    asset_tags = index[asset_id].get("tags", [])
    score = sum(1 for t in query_tags if t in asset_tags)
    scored.append((asset_id, score, index[asset_id]))

scored.sort(key=lambda x: x[1], reverse=True)

for aid, score, data in scored[:10]:
    print(f"{aid} (score={score}): {data['visual_description'][:60]}")
    print(f"  tags: {', '.join(data['tags'])}")
```

### Méthode 2 : Recherche sémantique via LLM (recommandée)

```python
import json, os, re
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Charger tous les assets
with open("F00_ASSET_FORGE/oracle_tags_vision.json") as f:
    vision_tags = json.load(f)

# Construire la liste pour le LLM
assets_list = []
for key, tags in sorted(vision_tags.items()):
    visual = tags.get("visual", "")
    narrative = ", ".join(tags.get("narrative", []))
    assets_list.append(f"{key} | {visual} | tags: {narrative}")

assets_text = "\n".join(assets_list)

# Recherche sémantique
query = "Category 5 hurricane making landfall with extreme destruction"

response = client.chat.completions.create(
    model="google/gemma-3-12b-it",
    messages=[
        {"role": "system", "content": "Tu es un expert en recherche d'images."},
        {"role": "user", "content": f"""
Trouve les 5 meilleurs assets pour illustrer: "{query}"

Assets disponibles (ID | description | tags):
{assets_text}

Réponds en JSON:
{{
  "found": true/false,
  "message": "explication",
  "results": [
    {{"id": "frame_XXX", "score": 1-10, "reason": "pourquoi"}}
  ]
}}
"""}
    ],
    temperature=0.2,
    max_tokens=2000,
)

result = json.loads(re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL).group())
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### Méthode 3 : Recherche par mot-clé visuel

```python
# Chercher dans les descriptions visuelles
keyword = "flood"
for key, data in index.items():
    visual = data.get("visual_description", "").lower()
    if keyword in visual:
        print(f"{key}: {data['visual_description'][:70]}")
```

---

## SÉLECTION ET ORDONNANCEMENT

### Le principe

Le script est découpé en **segments**. Chaque segment reçoit **une image**. L'Oracle doit :

1. **Découper le script** en segments (une idée = un segment, ~5-15s)
2. **Pour chaque segment**, chercher l'asset qui illustre le mieux le contenu
3. **Ordonner** les assets pour créer un flux narratif cohérent
4. **Éviter les répétitions** (ne pas utiliser la même frame 3x de suite)

### Règles de sélection

| Règle | Explication |
|-------|-------------|
| **Pertinence** | L'image doit illustrer ce que le texte dit |
| **Variété** | Alterner satellite / terrain / personnes / graphiques |
| **Honnêteté** | Si aucun asset ne correspond, utiliser un asset générique (globe, carte) |
| **Transition** | Les premiers et derniers segments peuvent être des intro/outro |
| **Intensité** | Les segments de danger → images de destruction ; les segments calmes → satellite/data |

### Algorithme recommandé

```python
def select_assets_for_script(script_segments, tag_index, index, vision_tags):
    """
    Pour chaque segment du script, trouve le meilleur asset.
    Évite les répétitions.
    """
    selected = []
    used_assets = set()

    for i, segment in enumerate(script_segments):
        # 1. Extraire les mots-clés du segment
        keywords = extract_keywords(segment["text"])

        # 2. Chercher les assets correspondants
        candidates = search_by_keywords(keywords, tag_index, index)

        # 3. Filtrer les déjà utilisés
        available = [a for a in candidates if a not in used_assets]

        # 4. Prendre le meilleur
        if available:
            best = available[0]
            used_assets.add(best)
        else:
            # Fallback: asset générique
            best = "frame_001"  # globe par défaut

        selected.append({
            "segment_id": i + 1,
            "asset_id": best,
            "visual": index[best].get("visual_description", ""),
            "text": segment["text"],
        })

    return selected
```

---

## PRÉPARATION POUR F02/F03

### Le format roadmap.json

F03 SIGISMUND consomme un `roadmap.json` avec cette structure :

```json
{
  "meta": {
    "title": "Hurricane Categories Explained",
    "duration_seconds": 180,
    "fps": 30
  },
  "style": {
    "font_primary": "Cinzel",
    "font_accent": "Playfair Display",
    "subtitle_size": 44,
    "subtitle_position": "bottom",
    "subtitle_color": "#FFFFFF",
    "accent_color": "#FFD700",
    "background_color": "#F5F0E8",
    "grain_intensity": 0.15,
    "vignette": true,
    "subtitle_anim": true,
    "subtitle_anim_speed": 5,
    "overlay_global_intensity": 3
  },
  "timeline": [
    {
      "id": 1,
      "image_file": "frame_000001.png",
      "text_subtitles": "Tropical storm. A tropical storm has sustained winds between 39 and 73 miles per hour.",
      "start_frame": 0,
      "end_frame": 270,
      "start": 0.0,
      "end": 9.0,
      "overlay_type": "defaut",
      "overlay_intensite": 2
    },
    {
      "id": 2,
      "image_file": "frame_000050.png",
      "text_subtitles": "This is the stage at which the system receives a name from a predetermined list.",
      "start_frame": 270,
      "end_frame": 540,
      "start": 9.0,
      "end": 18.0,
      "overlay_type": "vent",
      "overlay_intensite": 1
    }
  ],
  "validated_by_magos": true
}
```

### Correspondance F00 → F03

| Champ roadmap.json | Source F00 | Notes |
|--------------------|------------|-------|
| `image_file` | `BANK_B_NATURE/fire/frame_000XXX.png` | Copier dans `F03_SIGISMUND/CODEBASE/public/images/` |
| `text_subtitles` | Texte du script | Un segment = une phrase/idée |
| `start_frame` / `end_frame` | Calculé depuis `timing.json` (F01) | `frame = secondes × fps` |
| `start` / `end` | Timing audio (F01) | En secondes |
| `overlay_type` | Choix de l'Oracle | Voir types d'overlay ci-dessous |
| `overlay_intensite` | Choix de l'Oracle | 1=léger, 2=moyen, 3=intense |

### Types d'overlay disponibles (F03)

| overlay_type | Effet | Quand l'utiliser |
|--------------|-------|------------------|
| `defaut` | Aucun overlay spécial | Par défaut |
| `pluie` | Pluie animée sur l'image | Tempête, cyclone |
| `vent` | Effet de vent | Ouragan, vents forts |
| `soleil` | Éclairage solaire | Temps clair, chaleur |
| `vitre_pluie` | Pluie sur vitre | POV dans un véhicule |
| `neons_int` | Néons intérieurs | Scène urbaine nocturne |
| `lampe_int` | Lampe intérieure | Scène intime, interview |

### Pipeline de préparation

```
1. Script textuel
   ↓
2. F01 GRIMALDUS → audio_clean.mp3 + timing.json
   ↓
3. Oracle :
   a. Découper le script en segments (selon timing.json)
   b. Pour chaque segment, chercher l'asset F00
   c. Assigner overlay_type + overlay_intensite
   d. Produire roadmap.json
   ↓
4. Copier les images sélectionnées → F03/public/images/
   ↓
5. F03 SIGISMUND → rendu MP4 final
```

---

## EXEMPLE COMPLET

### Script : "Hurricane Categories"

```python
import json

# === 1. CHARGER LES DONNÉES F00 ===
with open("F00_ASSET_FORGE/index.json") as f:
    index = json.load(f)
with open("F00_ASSET_FORGE/tag_index.json") as f:
    tag_index = json.load(f)

# === 2. CHARGER LE TIMING F01 ===
with open("F01/OUT/timing.json") as f:
    timing = json.load(f)

# === 3. DÉCOUPER LE SCRIPT EN SEGMENTS ===
script_segments = [
    {"text": "Tropical storm. A tropical storm has sustained winds between 39 and 73 miles per hour.", "keywords": ["tempete", "vent"]},
    {"text": "This is the stage at which the system receives a name from the World Meteorological Organization.", "keywords": ["satellite", "donnees"]},
    {"text": "Category 1 hurricane. Sustained winds between 74 and 95 miles per hour.", "keywords": ["ouragan", "vent"]},
    {"text": "Hurricane Dolly in 2008 caused over 1.5 billion dollars in damage.", "keywords": ["destruction", "inondation"]},
    {"text": "Category 3 hurricane. The threshold for a major hurricane.", "keywords": ["ouragan", "danger"]},
    {"text": "Hurricane Katrina made landfall as a Category 3 in 2005.", "keywords": ["destruction", "inondation", "danger"]},
    {"text": "Category 5 hurricane. The highest classification on the Saffir-Simpson scale.", "keywords": ["ouragan", "destruction", "danger"]},
    {"text": "Hurricane Irma maintained Category 5 intensity for 37 consecutive hours.", "keywords": ["satellite", "tempete", "ouragan"]},
    {"text": "A single hurricane releases the energy equivalent of roughly 10,000 nuclear bombs per day.", "keywords": ["animation", "graphique", "donnees"]},
]

# === 4. SÉLECTIONNER LES ASSETS ===
selected = []
used = set()

for seg in script_segments:
    candidates = set()
    for kw in seg["keywords"]:
        if kw in tag_index:
            candidates.update(tag_index[kw])

    # Filtrer déjà utilisés + scorer
    available = [(a, sum(1 for k in seg["keywords"] if k in index.get(a, {}).get("tags", [])))
                 for a in candidates if a not in used]
    available.sort(key=lambda x: x[1], reverse=True)

    if available:
        best = available[0][0]
        used.add(best)
    else:
        best = "frame_001"  # fallback globe

    selected.append({
        "asset_id": best,
        "visual": index.get(best, {}).get("visual_description", ""),
        "text": seg["text"],
        "keywords": seg["keywords"],
    })

# === 5. CONSTRUIRE LE ROADMAP.JSON ===
fps = 30
roadmap = {
    "meta": {"title": "Hurricane Categories", "fps": fps},
    "style": {
        "font_primary": "Cinzel",
        "font_accent": "Playfair Display",
        "subtitle_size": 44,
        "subtitle_position": "bottom",
        "subtitle_color": "#FFFFFF",
        "accent_color": "#FFD700",
        "background_color": "#F5F0E8",
        "grain_intensity": 0.15,
        "vignette": True,
        "subtitle_anim": True,
        "subtitle_anim_speed": 5,
        "overlay_global_intensity": 3,
    },
    "timeline": [],
    "validated_by_magos": True,
}

# Mapper avec le timing
for i, sel in enumerate(selected):
    t_seg = timing["segments"][i] if i < len(timing.get("segments", [])) else {}
    start = t_seg.get("start", i * 9.0)
    end = t_seg.get("end", (i + 1) * 9.0)

    # Déterminer l'overlay
    keywords = sel["keywords"]
    if "pluie" in keywords or "inondation" in keywords:
        overlay_type = "pluie"
        overlay_intensite = 3
    elif "vent" in keywords or "ouragan" in keywords:
        overlay_type = "vent"
        overlay_intensite = 2
    elif "satellite" in keywords:
        overlay_type = "defaut"
        overlay_intensite = 1
    else:
        overlay_type = "defaut"
        overlay_intensite = 2

    # Convertir l'asset_id en nom de fichier
    asset_num = int(sel["asset_id"].split("_")[1])
    image_file = f"frame_{asset_num:06d}.png"

    roadmap["timeline"].append({
        "id": i + 1,
        "image_file": image_file,
        "text_subtitles": sel["text"],
        "start_frame": int(start * fps),
        "end_frame": int(end * fps),
        "start": start,
        "end": end,
        "overlay_type": overlay_type,
        "overlay_intensite": overlay_intensite,
    })

# === 6. SAUVEGARDER ===
with open("F02/OUT/roadmap.json", "w") as f:
    json.dump(roadmap, f, indent=2, ensure_ascii=False)

# === 7. COPIER LES IMAGES ===
import shutil, os
os.makedirs("F03_SIGISMUND/CODEBASE/public/images", exist_ok=True)
for seg in roadmap["timeline"]:
    src = f"F00_ASSET_FORGE/BANK_B_NATURE/fire/{seg['image_file']}"
    dst = f"F03_SIGISMUND/CODEBASE/public/images/{seg['image_file']}"
    if os.path.exists(src):
        shutil.copy(src, dst)

print(f"✅ roadmap.json créé: {len(roadmap['timeline'])} segments")
print(f"✅ {len(roadmap['timeline'])} images copiées")
```

---

## RÉFÉRENCE DES FICHIERS

### Arborescence CRUSADER

```
CRUSADER/
├── .github/workflows/
│   ├── f00_asset_forge.yml      # Ingest + Extract + Vision Tag
│   ├── f01_grimaldus.yml        # Voice processing
│   ├── f03_render.yml           # Remotion render
│   └── f03_vibeforge.yml        # Vibeforge variant
├── F00_ASSET_FORGE/
│   ├── BANK_B_NATURE/fire/      # Frames PNG + GIFs
│   ├── BANK_D_CLIPS/            # Clips MP4
│   ├── CANVAS/                  # Grilles de contact
│   ├── CODEBASE/                # Scripts Python
│   │   ├── crs_f00_ingest.py
│   │   ├── crs_f00_extract.py
│   │   ├── crs_f00_process.py
│   │   ├── crs_f00_index.py
│   │   ├── crs_f00_canvas.py
│   │   ├── crs_f00_vision_tagger.py
│   │   └── crs_f00_tagindex.py
│   ├── index.json               # Métadonnées + tags
│   ├── tag_index.json           # Reverse-index tag → assets
│   └── oracle_tags_vision.json  # Tags bruts vision IA
├── alpha/F02_CASTELLAN/OUT/
│   └── roadmap.json             # Exemple de roadmap
├── alpha/F03_SIGISMUND/CODEBASE/
│   ├── src/
│   │   ├── Main.jsx             # Composition Remotion
│   │   ├── components/
│   │   │   ├── Background.jsx   # Fond + grain + vignette
│   │   │   ├── Scene.jsx        # Image + Ken Burns + overlay
│   │   │   ├── Subtitle.jsx     # Sous-titres animés
│   │   │   └── overlays/        # Effets (pluie, vent, etc.)
│   │   └── Root.jsx
│   ├── crs_f03_sigismund.py     # Lanceur de rendu
│   └── public/
│       ├── images/              # Assets sélectionnés par l'Oracle
│       ├── audio/               # audio_clean.mp3
│       └── fonts/               # Polices .woff2
```

### Secrets GitHub requis

| Secret | Utilisé par | Obtenir sur |
|--------|-------------|-------------|
| `OPENROUTER_API_KEY` | F00 Vision Tagger | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GITHUB_TOKEN` | F03 (auto) | Automatique |

### Modèles de vision disponibles

| Modèle | Prix | Rate limit | Qualité |
|--------|------|------------|---------|
| `google/gemma-3-12b-it` | $0/token | 20 req/min | Bonne ✅ |
| `google/gemma-3-27b-it` | $0.0000001/tok | 20 req/min | Très bonne |
| `qwen/qwen3.5-flash-02-23` | $0.0000001/tok | 20 req/min | Bonne |

---

## CHECKLIST ORACLE

- [ ] Le script est découpé en segments
- [ ] Chaque segment a des mots-clés extraits
- [ ] Les assets sont recherchés dans `tag_index.json`
- [ ] Aucun asset n'est répété (sauf si intentionnel)
- [ ] Les overlays sont assignés selon le contenu
- [ ] Le `roadmap.json` est généré avec le bon format
- [ ] Les images sont copiées dans `F03/public/images/`
- [ ] Le `timing.json` (F01) est cohérent avec les `start_frame`/`end_frame`

---

*Guide créé pour CRUSADER — F00 ASSET FORGE → F03 SIGISMUND*
*Dernière mise à jour : 2026-07-12*
