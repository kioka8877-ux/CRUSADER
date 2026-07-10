#!/usr/bin/env python3
"""
CRS F00 — CANVAS
Crée une "toile" (contact sheet) avec toutes les frames + GIFs d'un run.
La toile est une seule grande image PNG numérotée que l'oracle (Claude vision)
peut analyser en un seul appel pour tagger tous les actifs.

Sortie :
  - canvas_frames.png  (grid numéroté de toutes les frames)
  - canvas_gifs.png    (grid numéroté des GIFs — 2 frames clés par GIF)
  - canvas_manifest.json (mapping numéro → fichier, pour le parsing)
"""

import os
import sys
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# === CONFIG ===
THUMB_W = 256          # largeur thumbnail
THUMB_H = 144          # hauteur thumbnail (16:9)
LABEL_H = 28           # hauteur label
PADDING = 4            # padding entre cellules
BG_COLOR = (20, 20, 20)
LABEL_BG = (40, 40, 40)
LABEL_FG = (255, 255, 0)  # jaune pour bien visible
MAX_COLS = 15          # max colonnes par rangée


def get_font(size=16):
    """Récupère une font lisible."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def create_frames_canvas(frames_dir: str, output_path: str) -> dict:
    """
    Crée une toile avec toutes les frames d'un dossier.
    Retourne un manifest {numéro: chemin_fichier}.
    """
    # Lister les frames triées
    frames = sorted(Path(frames_dir).glob("frame_*.png"))
    if not frames:
        print(f"[CANVAS] Aucune frame dans {frames_dir}")
        return {}

    count = len(frames)
    cols = min(MAX_COLS, count)
    rows = math.ceil(count / cols)

    cell_w = THUMB_W + PADDING
    cell_h = THUMB_H + LABEL_H + PADDING

    canvas_w = cols * cell_w + PADDING
    canvas_h = rows * cell_h + PADDING

    print(f"[CANVAS] Frames: {count} → grid {cols}×{rows} → {canvas_w}×{canvas_h}px")

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    font = get_font(14)

    manifest = {}

    for i, frame_path in enumerate(frames):
        num = i + 1
        col = i % cols
        row = i // cols

        x = PADDING + col * cell_w
        y = PADDING + row * cell_h

        # Charger et resize la frame
        try:
            img = Image.open(frame_path).convert("RGB")
            img = img.resize((THUMB_W, THUMB_H), Image.LANCZOS)
            canvas.paste(img, (x, y))
        except Exception as e:
            print(f"[CANVAS] Erreur frame {num}: {e}")
            # Dessiner un placeholder
            draw.rectangle([x, y, x + THUMB_W, y + THUMB_H], fill=(60, 0, 0))

        # Label avec numéro
        label_y = y + THUMB_H
        draw.rectangle([x, label_y, x + THUMB_W, label_y + LABEL_H], fill=LABEL_BG)
        label_text = str(num)
        draw.text((x + 5, label_y + 5), label_text, fill=LABEL_FG, font=font)

        # Enregistrer dans le manifest
        manifest[str(num)] = str(frame_path)

    # Sauvegarder
    canvas.save(output_path, "PNG", optimize=True)
    size_mb = os.path.getsize(output_path) / 1e6
    print(f"[CANVAS] Toile frames sauvegardée: {output_path} ({size_mb:.1f} MB)")

    return manifest


def create_gifs_canvas(gifs_dir: str, output_path: str) -> dict:
    """
    Crée une toile avec les GIFs — extrait 2 frames clés par GIF (début + milieu).
    Retourne un manifest {numéro: chemin_gif}.
    """
    gifs = sorted(Path(gifs_dir).glob("*.gif"))
    if not gifs:
        print(f"[CANVAS] Aucun GIF dans {gifs_dir}")
        return {}

    # Pour chaque GIF, extraire 2 frames (début + milieu)
    gif_thumbs = []  # liste de (gif_path, frame_start, frame_mid)

    for gif_path in gifs:
        try:
            gif = Image.open(gif_path)
            frame_count = 0
            frames = []

            while True:
                try:
                    frame = gif.convert("RGB")
                    frames.append(frame.copy())
                    frame_count += 1
                    gif.seek(gif.tell() + 1)
                except EOFError:
                    break

            if frame_count >= 2:
                mid_idx = frame_count // 2
                gif_thumbs.append((str(gif_path), frames[0], frames[mid_idx]))
            elif frame_count == 1:
                gif_thumbs.append((str(gif_path), frames[0], frames[0]))
            else:
                print(f"[CANVAS] GIF vide: {gif_path}")
        except Exception as e:
            print(f"[CANVAS] Erreur GIF {gif_path}: {e}")

    if not gif_thumbs:
        return {}

    count = len(gif_thumbs)
    # 2 thumbnails par GIF côte à côte
    pair_w = THUMB_W * 2 + PADDING
    cols = min(MAX_COLS, count)
    rows = math.ceil(count / cols)

    cell_w = pair_w + PADDING
    cell_h = THUMB_H + LABEL_H + PADDING

    canvas_w = cols * cell_w + PADDING
    canvas_h = rows * cell_h + PADDING

    print(f"[CANVAS] GIFs: {count} → grid {cols}×{rows} → {canvas_w}×{canvas_h}px")

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    font = get_font(14)

    manifest = {}

    for i, (gif_path, frame_start, frame_mid) in enumerate(gif_thumbs):
        num = i + 1
        col = i % cols
        row = i // cols

        x = PADDING + col * cell_w
        y = PADDING + row * cell_h

        # Frame début
        thumb_start = frame_start.resize((THUMB_W, THUMB_H), Image.LANCZOS)
        canvas.paste(thumb_start, (x, y))

        # Frame milieu
        thumb_mid = frame_mid.resize((THUMB_W, THUMB_H), Image.LANCZOS)
        canvas.paste(thumb_mid, (x + THUMB_W + PADDING, y))

        # Label
        label_y = y + THUMB_H
        draw.rectangle([x, label_y, x + pair_w, label_y + LABEL_H], fill=LABEL_BG)
        label_text = f"GIF {num}"
        draw.text((x + 5, label_y + 5), label_text, fill=LABEL_FG, font=font)

        manifest[str(num)] = gif_path

    canvas.save(output_path, "PNG", optimize=True)
    size_mb = os.path.getsize(output_path) / 1e6
    print(f"[CANVAS] Toile GIFs sauvegardée: {output_path} ({size_mb:.1f} MB)")

    return manifest


def create_canvas_for_bank(bank_dir: str, output_dir: str, source_name: str = "") -> dict:
    """
    Crée les toiles (frames + GIFs) pour une banque donnée.
    Retourne un manifest complet.
    """
    os.makedirs(output_dir, exist_ok=True)

    prefix = source_name or Path(bank_dir).name
    manifest = {"source": source_name, "frames": {}, "gifs": {}}

    # Toile frames
    frames_canvas_path = os.path.join(output_dir, f"canvas_frames_{prefix}.png")
    frames_manifest = create_frames_canvas(bank_dir, frames_canvas_path)
    manifest["frames"] = {
        "canvas_file": frames_canvas_path if frames_manifest else None,
        "mapping": frames_manifest
    }

    # Toile GIFs (chercher les GIFs dans le même dossier)
    gifs_canvas_path = os.path.join(output_dir, f"canvas_gifs_{prefix}.png")
    gifs_manifest = create_gifs_canvas(bank_dir, gifs_canvas_path)
    manifest["gifs"] = {
        "canvas_file": gifs_canvas_path if gifs_manifest else None,
        "mapping": gifs_manifest
    }

    # Sauvegarder le manifest
    manifest_path = os.path.join(output_dir, f"canvas_manifest_{prefix}.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[CANVAS] Manifest sauvegardé: {manifest_path}")

    return manifest


def create_canvas_all_banks(forge_root: str, output_dir: str = None) -> list[dict]:
    """
    Parcourt toutes les banques et crée les toiles pour chaque sous-dossier
    qui contient des frames ou des GIFs.
    """
    if output_dir is None:
        output_dir = os.path.join(forge_root, "CANVAS")

    os.makedirs(output_dir, exist_ok=True)

    all_manifests = []

    # Parcourir BANK_A, BANK_B, BANK_C, BANK_D
    banks = [
        ("BANK_A_CHARACTERS", "characters"),
        ("BANK_B_NATURE", "nature"),
        ("BANK_C_BACKGROUNDS", "backgrounds"),
        ("BANK_D_CLIPS", "clips"),
    ]

    for bank_name, category in banks:
        bank_path = os.path.join(forge_root, bank_name)
        if not os.path.exists(bank_path):
            continue

        # Parcourir les sous-dossiers
        for sub in sorted(os.listdir(bank_path)):
            sub_path = os.path.join(bank_path, sub)
            if not os.path.isdir(sub_path):
                continue

            # Vérifier s'il y a des PNG ou GIF
            has_png = any(Path(sub_path).glob("*.png"))
            has_gif = any(Path(sub_path).glob("*.gif"))

            if not has_png and not has_gif:
                continue

            source_name = f"{category}_{sub}"
            print(f"\n[CANVAS] Traitement: {source_name}")

            manifest = create_canvas_for_bank(sub_path, output_dir, source_name)
            manifest["bank"] = bank_name
            manifest["category"] = category
            manifest["subcategory"] = sub
            all_manifests.append(manifest)

    # Manifest global
    global_manifest_path = os.path.join(output_dir, "canvas_manifest_global.json")
    with open(global_manifest_path, "w") as f:
        json.dump(all_manifests, f, indent=2)
    print(f"\n[CANVAS] Manifest global: {global_manifest_path}")
    print(f"[CANVAS] {len(all_manifests)} banque(s) traitée(s)")

    return all_manifests


# === Prompt template pour l'oracle ===
ORACLE_PROMPT_FRAMES = """Tu es un archiviste visuel. Voici un "contact sheet" de {count} frames 
extraites d'une vidéo source: "{source}".

Chaque cellule est numérotée (1 à {count}). Pour CHAQUE frame numérotée, fournis :
- "visual": description visuelle en 5-10 mots (ex: "person running in heavy rain")
- "narrative": 2-3 tags narratifs — ce que l'image peut illustrer (ex: ["danger", "urgence", "météo"])
- "usage": 1-2 tags d'usage — comment l'utiliser (ex: ["illustration", "transition"])

Réponds en JSON strict, sans texte avant ou après :
{
  "1": {{"visual": "...", "narrative": ["...", "..."], "usage": ["...", "..."]}},
  "2": {{"visual": "...", "narrative": ["...", "..."], "usage": ["...", "..."]}},
  ...
}
"""

ORACLE_PROMPT_GIFS = """Tu es un archiviste visuel. Voici un "contact sheet" de {count} GIFs animés.
Pour chaque GIF, 2 frames sont affichées côte à côte (début + milieu de l'animation).
Chaque GIF est numéroté (GIF 1 à GIF {count}).

Pour CHAQUE GIF numéroté, fournis :
- "visual": description de l'animation en 5-10 mots (ex: "rain falling with wind blowing")
- "narrative": 2-3 tags narratifs
- "usage": 1-2 tags d'usage

Réponds en JSON strict :
{
  "1": {{"visual": "...", "narrative": ["...", "..."], "usage": ["...", "..."]}},
  "2": {{"visual": "...", "narrative": ["...", "..."], "usage": ["...", "..."]}},
  ...
}
"""


def generate_oracle_prompt(manifest: dict, canvas_type: str = "frames") -> str:
    """
    Génère le prompt à envoyer à l'oracle (Claude vision).
    """
    if canvas_type == "frames":
        count = len(manifest.get("frames", {}).get("mapping", {}))
        source = manifest.get("source", "unknown")
        return ORACLE_PROMPT_FRAMES.format(count=count, source=source)
    elif canvas_type == "gifs":
        count = len(manifest.get("gifs", {}).get("mapping", {}))
        source = manifest.get("source", "unknown")
        return ORACLE_PROMPT_GIFS.format(count=count, source=source)
    return ""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="F00 CANVAS — Create contact sheet for oracle vision tagging")
    parser.add_argument("--forge-root", default="..", help="Racine F00_ASSET_FORGE")
    parser.add_argument("--output", default=None, help="Dossier de sortie (défaut: {forge_root}/CANVAS)")
    parser.add_argument("--bank", default=None, help="Banque spécifique à traiter (ex: BANK_B_NATURE/fire)")
    parser.add_argument("--prompt-only", action="store_true", help="Génère seulement les prompts pour l'oracle")
    args = parser.parse_args()

    if args.bank:
        # Mode banque spécifique
        bank_path = os.path.join(args.forge_root, args.bank)
        output = args.output or os.path.join(args.forge_root, "CANVAS")
        manifest = create_canvas_for_bank(bank_path, output, args.bank.replace("/", "_"))
        if not args.prompt_only:
            print("\n=== PROMPT ORACLE (FRAMES) ===")
            print(generate_oracle_prompt(manifest, "frames"))
            print("\n=== PROMPT ORACLE (GIFS) ===")
            print(generate_oracle_prompt(manifest, "gifs"))
    else:
        # Mode toutes les banques
        manifests = create_canvas_all_banks(args.forge_root, args.output)

        if args.prompt_only:
            print("\n" + "="*60)
            print("PROMPTS POUR L'ORACLE")
            print("="*60)
            for m in manifests:
                print(f"\n--- {m['category']}/{m['subcategory']} ---")
                print("\n[FRAMES]")
                print(generate_oracle_prompt(m, "frames"))
                print("\n[GIFS]")
                print(generate_oracle_prompt(m, "gifs"))
