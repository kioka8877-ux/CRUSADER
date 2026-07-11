#!/usr/bin/env python3
"""
CRS F00 — VISION TAGGER (OpenRouter)
Analyse les canvases rangée par rangée avec un modèle vision via OpenRouter.
API OpenAI-compatible → utilise le SDK openai.

Modèle: google/gemma-3-12b-it (gratuit, $0/token, vision)
Stratégie: envoyer chaque RANGÉE du canvas (15 cellules) séparément.
- 255 frames / 15 = 17 rangées + 2 rangées GIFs = ~19 appels
- Rate limit OpenRouter: 20 req/min (largement suffisant)

Usage:
  python crs_f00_vision_tagger.py --forge-root .. --output ../oracle_tags_vision.json

Prérequis:
  - OPENROUTER_API_KEY dans l'environnement (secret GitHub)
  - pip install openai pillow
"""

import os
import sys
import json
import time
import re
import base64
import io
import argparse
from datetime import datetime, timezone

try:
    from openai import OpenAI
    from PIL import Image
except ImportError as e:
    print(f"[VISION] ERREUR: dépendance manquante: {e}")
    print("[VISION] Installer avec: pip install openai pillow")
    sys.exit(1)


# === CONFIG ===
MODEL_NAME = "google/gemma-3-12b-it"
RATE_LIMIT_DELAY = 3  # secondes entre chaque appel
MAX_RETRIES = 3
RETRY_DELAY = 10  # secondes
MAX_ROW_WIDTH = 2048
CELLS_PER_ROW = 15

# Config canvas (doit correspondre à crs_f00_canvas.py)
THUMB_W = 256
THUMB_H = 144
LABEL_H = 28
PADDING = 4
CELL_W = THUMB_W + PADDING  # 260
CELL_H = THUMB_H + LABEL_H + PADDING  # 176


# === PROMPT ===
ROW_PROMPT = """You are looking at a single ROW from a contact sheet of video frames from a NASA/GPM educational video about hurricanes, floods, and satellite weather data.

This row contains exactly 15 cells, numbered left to right starting from {start_num}.
Each cell has a yellow number label and a video frame thumbnail.

For EACH of the 15 cells, provide a JSON object:
- "n": cell number (integer, starting from {start_num})
- "v": 5-8 word English description of what you see in the frame
- "t": array of 2-3 French storytelling tags (choose from: danger, secours, satellite, tempete, inondation, science, technologie, mesure, prevision, alerte, population, infrastructure, expertise, donnees, nature, humanite, espoir, destruction, ouragan, vent, pluie, eau, carte, globe, animation, graphique, interview, explication, intro, transition)
- "u": single usage tag string (one of: illustration, transition, background, overlay, intro, outro, b-roll)

Return a JSON array of 15 objects. Be accurate - only describe what you actually see."""


def robust_json_parse(text: str) -> list:
    """Parse la réponse JSON de manière robuste."""
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
        fragment = re.sub(r',\s*]', ']', fragment)
        fragment = re.sub(r',\s*}', '}', fragment)
        try:
            return json.loads(fragment)
        except:
            pass

    # Extraire objets individuels avec regex
    objects = re.findall(r'\{[^}]+\}', text)
    results = []
    for obj_str in objects:
        try:
            obj = json.loads(obj_str)
            if isinstance(obj.get("u"), list):
                obj["u"] = obj["u"][0] if obj["u"] else "illustration"
            if isinstance(obj.get("t"), str):
                obj["t"] = [obj["t"]]
            results.append(obj)
        except:
            n_match = re.search(r'"n"\s*:\s*(\d+)', obj_str)
            v_match = re.search(r'"v"\s*:\s*"([^"]*)"', obj_str)
            if n_match:
                t_section = re.search(r'"t"\s*:\s*\[([^\]]*)\]', obj_str)
                tags = re.findall(r'"([^"]*)"', t_section.group(1)) if t_section else []
                results.append({
                    "n": int(n_match.group(1)),
                    "v": v_match.group(1) if v_match else "",
                    "t": [t for t in tags if not t.isdigit() and len(t) > 1][:3],
                    "u": "illustration"
                })
    return results


def image_to_base64(img: Image.Image) -> str:
    """Convertit une PIL Image en base64 JPEG."""
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def extract_row_from_canvas(canvas_img, row_idx: int, total_rows: int) -> Image.Image:
    """Extrait une rangée du canvas."""
    w, h = canvas_img.size
    row_h = h // total_rows
    y_start = row_idx * row_h
    y_end = (row_idx + 1) * row_h if row_idx < total_rows - 1 else h
    return canvas_img.crop((0, y_start, w, y_end))


def analyze_row(client, row_img: Image.Image, start_num: int) -> list:
    """Envoie une rangée à OpenRouter Vision et récupère les tags."""
    # Redimensionner si trop grand
    if row_img.size[0] > MAX_ROW_WIDTH:
        ratio = MAX_ROW_WIDTH / row_img.size[0]
        new_size = (int(row_img.size[0] * ratio), int(row_img.size[1] * ratio))
        row_img = row_img.resize(new_size, Image.LANCZOS)

    if row_img.mode in ('RGBA', 'P'):
        row_img = row_img.convert('RGB')

    img_b64 = image_to_base64(row_img)
    prompt = ROW_PROMPT.format(start_num=start_num)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=4000,
            )

            text = response.choices[0].message.content.strip()
            results = robust_json_parse(text)

            # Normaliser
            for r in results:
                if isinstance(r.get("u"), list):
                    r["u"] = r["u"][0] if r["u"] else "illustration"
                if isinstance(r.get("t"), str):
                    r["t"] = [r["t"]]

            return results

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                wait_time = RETRY_DELAY * (attempt + 2)
                print(f"  ⚠️ Rate limit, attente {wait_time}s... (tentative {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            elif attempt < MAX_RETRIES - 1:
                print(f"  ⚠️ Erreur (tentative {attempt+1}): {error_str[:80]}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ❌ Échec: {error_str[:100]}")
                return []

    return []


def find_canvases(forge_root: str) -> list:
    """Trouve tous les canvases à analyser."""
    canvases = []

    canvas_dir = os.path.join(forge_root, "CANVAS")
    if os.path.exists(canvas_dir):
        for f in sorted(os.listdir(canvas_dir)):
            if f.startswith("canvas_frames") and f.endswith(".png"):
                canvases.append(("frames", os.path.join(canvas_dir, f)))
            elif f.startswith("canvas_gifs") and f.endswith(".png"):
                canvases.append(("gifs", os.path.join(canvas_dir, f)))

    # Fallback: .uploads/
    if not canvases:
        upload_dir = "/home/user/.uploads"
        if os.path.exists(upload_dir):
            for f in sorted(os.listdir(upload_dir)):
                if f.startswith("canvas_band") and f.endswith((".png", ".jpg")):
                    canvases.append(("frames", os.path.join(upload_dir, f)))
                elif f.startswith("canvas_gifs") and f.endswith((".png", ".jpg")):
                    canvases.append(("gifs", os.path.join(upload_dir, f)))

    return canvases


def process_all_canvases(forge_root: str, output_path: str):
    """Analyse tous les canvases rangée par rangée."""
    canvases = find_canvases(forge_root)

    if not canvases:
        print("[VISION] ERREUR: Aucun canvas trouvé!")
        return {}

    print(f"\n[VISION] {len(canvases)} canvases à analyser")

    # Configurer OpenRouter
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("[VISION] ERREUR: OPENROUTER_API_KEY non défini")
        sys.exit(1)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    print(f"[VISION] OpenRouter configuré: {MODEL_NAME}")

    # Charger tags existants (mode reprise)
    all_tags = {}
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            all_tags = json.load(f)
        print(f"[VISION] {len(all_tags)} tags existants chargés (mode reprise)")

    total_api_calls = 0

    for canvas_type, canvas_path in canvases:
        canvas_name = os.path.basename(canvas_path)
        canvas_img = Image.open(canvas_path)
        w, h = canvas_img.size

        # Déterminer le nombre de rangées
        total_rows = h // CELL_H
        if h % CELL_H > CELL_H // 2:
            total_rows += 1

        # Offset de numérotation
        offset = 0
        if "band2" in canvas_name.lower():
            offset = 90
        elif "band3" in canvas_name.lower():
            offset = 180
        if "nature_fire" in canvas_name.lower() and canvas_type == "frames":
            offset = 0

        print(f"\n[VISION] === {canvas_name} ({w}×{h}) ===")
        print(f"  Type: {canvas_type} | Rangées: {total_rows} | Offset: {offset}")

        for row_idx in range(total_rows):
            start_num = (row_idx * CELLS_PER_ROW) + 1 + offset
            row_name = f"rangée {row_idx+1}/{total_rows} (cells {start_num}-{start_num+CELLS_PER_ROW-1})"

            # Skip si déjà taggé
            all_done = True
            for c in range(CELLS_PER_ROW):
                cell_num = start_num + c
                if canvas_type == "gifs":
                    asset_id = f"gif_{cell_num:02d}"
                else:
                    asset_id = f"frame_{cell_num:03d}"
                if asset_id not in all_tags or "erreur" in str(all_tags.get(asset_id, {}).get("narrative", [])):
                    all_done = False
                    break
            if all_done:
                print(f"  [{row_name}] déjà taggé, skip")
                continue

            print(f"  [{row_name}] analyse...", end=" ", flush=True)

            row_img = extract_row_from_canvas(canvas_img, row_idx, total_rows)
            results = analyze_row(client, row_img, start_num)
            total_api_calls += 1

            tagged_in_row = 0
            for r in results:
                cell_num = r.get("n", 0)
                if cell_num == 0:
                    continue

                if canvas_type == "gifs":
                    asset_id = f"gif_{cell_num:02d}"
                else:
                    asset_id = f"frame_{cell_num:03d}"

                narrative = r.get("t", [])
                if isinstance(narrative, str):
                    narrative = [narrative]

                usage = r.get("u", "illustration")
                if isinstance(usage, list):
                    usage = usage[0] if usage else "illustration"

                all_tags[asset_id] = {
                    "visual": r.get("v", ""),
                    "narrative": narrative,
                    "usage": usage,
                }
                tagged_in_row += 1

            print(f"✅ {tagged_in_row} cells")

            # Sauvegarder après chaque rangée
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_tags, f, indent=2, ensure_ascii=False)

            time.sleep(RATE_LIMIT_DELAY)

    # Résumé
    print(f"\n[VISION] === RÉSUMÉ ===")
    print(f"  Appels API: {total_api_calls}")
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
        narrative = tag_data.get("narrative", [])
        if isinstance(narrative, str):
            narrative = [narrative]

        usage = tag_data.get("usage", "illustration")
        if isinstance(usage, list):
            usage = usage[0] if usage else "illustration"

        if asset_id in index:
            index[asset_id]["tags"] = narrative
            index[asset_id]["visual_description"] = tag_data.get("visual", "")
            index[asset_id]["usage_tags"] = [usage]
            index[asset_id]["tagged_by"] = "openrouter-gemma-3-12b"
            index[asset_id]["tagged_at"] = datetime.now(timezone.utc).isoformat()
        else:
            index[asset_id] = {
                "type": "frame" if asset_id.startswith("frame_") else "gif",
                "tags": narrative,
                "visual_description": tag_data.get("visual", ""),
                "usage_tags": [usage],
                "tagged_by": "openrouter-gemma-3-12b",
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
        narrative = asset_data.get("tags", [])
        if isinstance(narrative, list):
            all_tags.extend(narrative)

        usage = asset_data.get("usage_tags", [])
        if isinstance(usage, list):
            all_tags.extend(usage)

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

    sorted_tags = sorted(tag_index.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"\n[VISION] Top 15 tags:")
    for i, (tag, assets) in enumerate(sorted_tags[:15], 1):
        print(f"  {i:2d}. {tag:25s} → {len(assets):3d} assets")


def main():
    parser = argparse.ArgumentParser(description="F00 Vision Tagger — OpenRouter (Gemma 3 12B)")
    parser.add_argument("--forge-root", default="..", help="Racine F00_ASSET_FORGE")
    parser.add_argument("--output", default="../oracle_tags_vision.json", help="Fichier de sortie")
    parser.add_argument("--index", default="../index.json", help="index.json à mettre à jour")
    parser.add_argument("--tag-index", default="../tag_index.json", help="tag_index.json à créer")
    parser.add_argument("--skip-index", action="store_true", help="Ne pas mettre à jour index.json")
    args = parser.parse_args()

    print("=" * 60)
    print("  F00 VISION TAGGER — OpenRouter (Gemma 3 12B)")
    print("=" * 60)

    tags = process_all_canvases(args.forge_root, args.output)

    if not tags:
        print("[VISION] Aucun tag généré — arrêt")
        return

    if not args.skip_index:
        print(f"\n[VISION] Mise à jour de {args.index}...")
        update_index(tags, args.index)
        print(f"\n[VISION] Construction du tag_index...")
        build_tag_index(args.index, args.tag_index)

    print(f"\n[VISION] ✅ Terminé !")


if __name__ == "__main__":
    main()
