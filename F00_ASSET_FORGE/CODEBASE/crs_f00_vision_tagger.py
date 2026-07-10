#!/usr/bin/env python3
"""
CRS F00 — VISION TAGGER (Gemini 2.5 Flash)
Analyse les canvases (grilles de frames) avec Gemini Vision API et assigne
des tags RÉELS basés sur ce que l'IA voit dans chaque cellule.

Stratégie: envoyer les canvases entiers (grilles 15×N) au lieu d'images
individuelles → 4 appels API au lieu de 281 → économise le quota.

Usage:
  python crs_f00_vision_tagger.py --forge-root .. --output ../oracle_tags_vision.json

Prérequis:
  - GEMINI_API_KEY dans l'environnement (secret GitHub)
  - pip install google-genai pillow

Sortie:
  - oracle_tags_vision.json : tags visuels pour chaque asset
  - Met à jour index.json avec les vrais tags
  - Met à jour tag_index.json (reverse-index)
"""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO

try:
    from google import genai
    from google.genai import types
    from PIL import Image
except ImportError as e:
    print(f"[VISION] ERREUR: dépendance manquante: {e}")
    print("[VISION] Installer avec: pip install google-genai pillow")
    sys.exit(1)


# === CONFIG ===
MODEL_NAME = "gemini-2.5-flash"
RATE_LIMIT_DELAY = 5  # secondes entre chaque appel canvas
MAX_RETRIES = 3
RETRY_DELAY = 30  # secondes (pour 429 rate limit)
MAX_CANVAS_WIDTH = 1536  # redimensionner pour Gemini


# === PROMPT ===
CANVAS_PROMPT = """You are looking at a contact sheet (grid) of video frames from a NASA/GPM educational video about hurricanes, floods, and satellite weather data.

The grid has 15 columns. Each cell contains one frame with a yellow number label.
Number the cells left-to-right, top-to-bottom starting from 1.

For EACH numbered cell, provide:
- "n": the cell number (integer)
- "v": 5-8 word English description of what you see
- "t": array of 2-3 French storytelling tags (from: danger, secours, satellite, tempete, inondation, science, technologie, mesure, prevision, alerte, population, infrastructure, expertise, donnees, nature, humanite, espoir, destruction, ouragan, vent, pluie, eau, carte, globe, animation, graphique, interview, explication, intro, transition)
- "u": 1 usage tag (illustration, transition, background, overlay, intro, outro, b-roll)

Return a JSON array of objects, one per cell. Be accurate - only describe what you actually see."""


def robust_json_parse(text: str) -> list:
    """
    Parse la réponse JSON de Gemini de manière robuste.
    Gère: markdown, troncature, virgules trailing, etc.
    """
    text = text.strip()

    # Retirer markdown ```json ... ```
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("[") or p.startswith("{"):
                text = p
                break

    # Essayer JSON direct
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except:
        pass

    # Extraire entre [ et ]
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        fragment = match.group()
        # Nettoyer virgules trailing
        fragment = re.sub(r',\s*]', ']', fragment)
        fragment = re.sub(r',\s*}', '}', fragment)
        try:
            return json.loads(fragment)
        except:
            pass

    # Dernier recours: extraire les objets individuels avec regex
    objects = re.findall(r'\{[^}]+\}', text)
    results = []
    for obj_str in objects:
        try:
            results.append(json.loads(obj_str))
        except:
            n_match = re.search(r'"n"\s*:\s*(\d+)', obj_str)
            v_match = re.search(r'"v"\s*:\s*"([^"]*)"', obj_str)
            t_match = re.findall(r'"([^"]*)"', obj_str)
            if n_match:
                results.append({
                    "n": int(n_match.group(1)),
                    "v": v_match.group(1) if v_match else "",
                    "t": [t for t in t_match if not t.isdigit() and len(t) > 1][:3],
                    "u": "illustration"
                })
    return results


def analyze_canvas(client, canvas_path: str, canvas_name: str) -> list:
    """
    Envoie un canvas (grille de frames) à Gemini Vision et récupère les tags.
    """
    img = Image.open(canvas_path)

    # Redimensionner si trop grand
    if img.size[0] > MAX_CANVAS_WIDTH:
        ratio = MAX_CANVAS_WIDTH / img.size[0]
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Convertir en RGB si nécessaire
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    print(f"  Canvas: {canvas_name} ({img.size[0]}×{img.size[1]})")

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[CANVAS_PROMPT, img],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=8000,
                    response_mime_type="application/json"
                )
            )

            results = robust_json_parse(response.text)
            print(f"  ✅ {len(results)} cells décrites")
            return results

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"  ⚠️ Rate limit, attente {wait_time}s... (tentative {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            elif attempt < MAX_RETRIES - 1:
                print(f"  ⚠️ Erreur (tentative {attempt+1}): {error_str[:80]}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ❌ Échec: {error_str[:100]}")
                return []

    return []


def process_all_canvases(forge_root: str, output_path: str):
    """
    Parcourt tous les canvases et les analyse avec Gemini Vision.
    """
    canvas_dir = os.path.join(forge_root, "CANVAS")

    # Chercher les canvases de frames
    canvas_files = []
    if os.path.exists(canvas_dir):
        for f in sorted(os.listdir(canvas_dir)):
            if f.startswith("canvas_frames") and f.endswith(".png"):
                canvas_files.append(("frames", os.path.join(canvas_dir, f)))
            elif f.startswith("canvas_gifs") and f.endswith(".png"):
                canvas_files.append(("gifs", os.path.join(canvas_dir, f)))

    # Fallback: utiliser les canvases de .uploads si CANVAS n'existe pas
    if not canvas_files:
        upload_dir = "/home/user/.uploads"
        for f in sorted(os.listdir(upload_dir)) if os.path.exists(upload_dir) else []:
            if f.startswith("canvas_band") and f.endswith((".png", ".jpg")):
                canvas_files.append(("frames", os.path.join(upload_dir, f)))
            elif f.startswith("canvas_gifs") and f.endswith((".png", ".jpg")):
                canvas_files.append(("gifs", os.path.join(upload_dir, f)))

    if not canvas_files:
        print("[VISION] ERREUR: Aucun canvas trouvé!")
        print(f"[VISION] Cherché dans: {canvas_dir}")
        return {}

    print(f"\n[VISION] {len(canvas_files)} canvases à analyser:")
    for ctype, cpath in canvas_files:
        print(f"  - {ctype}: {os.path.basename(cpath)}")

    # Configurer Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[VISION] ERREUR: GEMINI_API_KEY non défini")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    print(f"[VISION] Gemini configuré: {MODEL_NAME}")

    # Charger les tags existants (pour reprise)
    all_tags = {}
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            all_tags = json.load(f)
        print(f"[VISION] {len(all_tags)} tags existants chargés (mode reprise)")

    # Analyser chaque canvas
    for canvas_type, canvas_path in canvas_files:
        canvas_name = os.path.basename(canvas_path)
        print(f"\n[VISION] === {canvas_name} ===")

        # Déterminer le offset de numérotation
        # Band 1 = frames 1-90, Band 2 = frames 91-180, Band 3 = frames 181-255
        offset = 0
        if "band2" in canvas_name.lower():
            offset = 90
        elif "band3" in canvas_name.lower():
            offset = 180
        elif "gifs" in canvas_name.lower():
            offset = 0  # GIFs sont numérotés séparément

        results = analyze_canvas(client, canvas_path, canvas_name)

        # Convertir les résultats en tags par asset
        for r in results:
            cell_num = r.get("n", 0)
            if cell_num == 0:
                continue

            if canvas_type == "gifs":
                asset_id = f"gif_{cell_num:02d}"
            else:
                frame_num = cell_num + offset
                asset_id = f"frame_{frame_num:03d}"

            all_tags[asset_id] = {
                "visual": r.get("v", ""),
                "narrative": r.get("t", []),
                "usage": r.get("u", []),
            }

        # Sauvegarder après chaque canvas
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_tags, f, indent=2, ensure_ascii=False)
        print(f"  💾 Sauvegardé: {len(all_tags)} tags")

        # Rate limiting entre canvases
        time.sleep(RATE_LIMIT_DELAY)

    # Résumé
    print(f"\n[VISION] === RÉSUMÉ ===")
    print(f"  Total tags: {len(all_tags)}")
    frames_count = sum(1 for k in all_tags if k.startswith("frame_"))
    gifs_count = sum(1 for k in all_tags if k.startswith("gif_"))
    print(f"  Frames: {frames_count}")
    print(f"  GIFs: {gifs_count}")

    return all_tags


def update_index(tags: dict, index_path: str):
    """Met à jour index.json avec les tags visuels."""
    with open(index_path, "r") as f:
        index = json.load(f)

    updated = 0
    for asset_id, tag_data in tags.items():
        if asset_id in index:
            index[asset_id]["tags"] = tag_data.get("narrative", [])
            index[asset_id]["visual_description"] = tag_data.get("visual", "")
            index[asset_id]["usage_tags"] = tag_data.get("usage", [])
            index[asset_id]["tagged_by"] = "gemini-2.5-flash"
            index[asset_id]["tagged_at"] = datetime.now(timezone.utc).isoformat()
            updated += 1
        else:
            # Créer l'entrée si elle n'existe pas
            index[asset_id] = {
                "type": "frame" if asset_id.startswith("frame_") else "gif",
                "tags": tag_data.get("narrative", []),
                "visual_description": tag_data.get("visual", ""),
                "usage_tags": tag_data.get("usage", []),
                "tagged_by": "gemini-2.5-flash",
                "tagged_at": datetime.now(timezone.utc).isoformat(),
                "source": "F00 ASSET FORGE"
            }
            updated += 1

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"[VISION] index.json mis à jour: {updated} assets")


def build_tag_index(index_path: str, output_path: str):
    """Construit le reverse-index tag → [assets]."""
    with open(index_path, "r") as f:
        index = json.load(f)

    tag_index = {}
    for asset_id, asset_data in index.items():
        if not isinstance(asset_data, dict):
            continue

        all_tags = []
        all_tags.extend(asset_data.get("tags", []))
        all_tags.extend(asset_data.get("usage_tags", []))

        # Indexer aussi les mots de la description visuelle
        visual = asset_data.get("visual_description", "")
        if visual:
            words = [w.lower().strip(".,;:!?") for w in visual.split() if len(w) > 2]
            all_tags.extend(words)

        for tag in all_tags:
            tag_lower = tag.lower().strip()
            if not tag_lower or tag_lower == "erreur":
                continue
            if tag_lower not in tag_index:
                tag_index[tag_lower] = []
            if asset_id not in tag_index[tag_lower]:
                tag_index[tag_lower].append(asset_id)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tag_index, f, indent=2, ensure_ascii=False)

    print(f"[VISION] tag_index.json créé: {len(tag_index)} tags uniques")

    # Afficher top tags
    sorted_tags = sorted(tag_index.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"\n[VISION] Top 15 tags:")
    for i, (tag, assets) in enumerate(sorted_tags[:15], 1):
        print(f"  {i:2d}. {tag:25s} → {len(assets):3d} assets")


def main():
    parser = argparse.ArgumentParser(description="F00 Vision Tagger — Gemini 2.5 Flash")
    parser.add_argument("--forge-root", default="..", help="Racine F00_ASSET_FORGE")
    parser.add_argument("--output", default="../oracle_tags_vision.json", help="Fichier de sortie")
    parser.add_argument("--index", default="../index.json", help="index.json à mettre à jour")
    parser.add_argument("--tag-index", default="../tag_index.json", help="tag_index.json à créer")
    parser.add_argument("--skip-index", action="store_true", help="Ne pas mettre à jour index.json")
    args = parser.parse_args()

    print("=" * 60)
    print("  F00 VISION TAGGER — Gemini 2.5 Flash (Canvas Mode)")
    print("=" * 60)

    # Analyser tous les canvases
    tags = process_all_canvases(args.forge_root, args.output)

    if not tags:
        print("[VISION] Aucun tag généré — arrêt")
        return

    # Mettre à jour index.json
    if not args.skip_index:
        print(f"\n[VISION] Mise à jour de {args.index}...")
        update_index(tags, args.index)

        # Construire le tag_index
        print(f"\n[VISION] Construction du tag_index...")
        build_tag_index(args.index, args.tag_index)

    print(f"\n[VISION] ✅ Terminé !")
    print(f"  Tags: {args.output}")
    print(f"  Index: {args.index}")
    print(f"  Tag index: {args.tag_index}")


if __name__ == "__main__":
    main()
