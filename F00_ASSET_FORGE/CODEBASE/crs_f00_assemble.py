#!/usr/bin/env python3
"""
CRS F00 — ASSEMBLE
Composite : combine un personnage (BANK_A) + un décor (BANK_C) → visuel final.
Peut aussi ajouter un élément nature (BANK_B) par-dessus.
Le visuel final est copié vers {mode}/SHARED/IN/images/ pour le pipeline CRUSADER.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from PIL import Image


def load_index(forge_root: str) -> dict:
    """Charge index.json."""
    index_path = os.path.join(forge_root, "index.json")
    with open(index_path, "r") as f:
        return json.load(f)


def find_asset(index: dict, asset_id: str) -> dict | None:
    """Trouve un actif par son ID dans l'index."""
    for category in ["characters", "nature", "backgrounds", "clips"]:
        for asset in index.get(category, []):
            if asset["id"] == asset_id:
                return asset
    return None


def resolve_asset_path(forge_root: str, asset: dict) -> str:
    """Résout le chemin complet d'un actif."""
    return os.path.join(forge_root, asset["file"])


def composite_assets(
    background_path: str,
    character_path: str | None = None,
    nature_path: str | None = None,
    character_position: tuple = ("center", "bottom"),
    character_scale: float = 1.0,
    nature_opacity: float = 0.8,
    output_size: tuple = (1920, 1080)
) -> Image.Image:
    """
    Combine background + character + nature → visuel final.
    
    Args:
        background_path: Chemin du décor (BANK_C)
        character_path: Chemin du personnage PNG transparent (BANK_A), optionnel
        nature_path: Chemin d'un élément nature (BANK_B), optionnel
        character_position: Position du personnage ("center", "left", "right", "bottom", "top")
        character_scale: Échelle du personnage (1.0 = taille originale)
        nature_opacity: Opacité de l'élément nature (0.0-1.0)
        output_size: Taille du visuel final (1920x1080 par défaut)
    """
    # 1. Préparer le background
    bg = Image.open(background_path).convert("RGBA")
    bg = bg.resize(output_size, Image.LANCZOS)

    # 2. Ajouter le personnage si fourni
    if character_path and os.path.exists(character_path):
        char = Image.open(character_path).convert("RGBA")

        # Scale
        if character_scale != 1.0:
            new_size = (int(char.width * character_scale), int(char.height * character_scale))
            char = char.resize(new_size, Image.LANCZOS)

        # Position
        x, y = _resolve_position(char, output_size, character_position)
        bg.paste(char, (x, y), char)  # mask=char pour respecter la transparence

    # 3. Ajouter l'élément nature si fourni
    if nature_path and os.path.exists(nature_path):
        nature = Image.open(nature_path).convert("RGBA")
        nature = nature.resize(output_size, Image.LANCZOS)

        # Appliquer l'opacité
        if nature_opacity < 1.0:
            alpha = nature.split()[3]
            alpha = alpha.point(lambda p: int(p * nature_opacity))
            nature.putalpha(alpha)

        bg.paste(nature, (0, 0), nature)

    return bg


def _resolve_position(char: Image.Image, canvas_size: tuple,
                      position: tuple) -> tuple:
    """Calcule la position (x, y) selon les mots-clés."""
    cw, ch = canvas_size
    char_w, char_h = char.size

    h_pos, v_pos = position

    # Horizontal
    if h_pos == "center":
        x = (cw - char_w) // 2
    elif h_pos == "left":
        x = 0
    elif h_pos == "right":
        x = cw - char_w
    else:
        x = int(h_pos)

    # Vertical
    if v_pos == "center":
        y = (ch - char_h) // 2
    elif v_pos == "top":
        y = 0
    elif v_pos == "bottom":
        y = ch - char_h
    else:
        y = int(v_pos)

    return (x, y)


def assemble_single(
    forge_root: str,
    background_id: str,
    character_id: str | None = None,
    nature_id: str | None = None,
    output_path: str = "./assembled/scene_001.png",
    character_position: tuple = ("center", "bottom"),
    character_scale: float = 1.0,
    nature_opacity: float = 0.8,
    output_size: tuple = (1920, 1080)
) -> str:
    """
    Assemble un visuel final à partir d'IDs d'actifs de l'index.
    """
    index = load_index(forge_root)

    # Résoudre les assets
    bg_asset = find_asset(index, background_id)
    if not bg_asset:
        raise ValueError(f"Background {background_id} introuvable dans l'index")

    bg_path = resolve_asset_path(forge_root, bg_asset)

    char_path = None
    if character_id:
        char_asset = find_asset(index, character_id)
        if char_asset:
            char_path = resolve_asset_path(forge_root, char_asset)
        else:
            print(f"WARNING: Personnage {character_id} introuvable")

    nature_path = None
    if nature_id:
        nature_asset = find_asset(index, nature_id)
        if nature_asset:
            nature_path = resolve_asset_path(forge_root, nature_asset)
        else:
            print(f"WARNING: Nature {nature_id} introuvable")

    # Composite
    result = composite_assets(
        bg_path, char_path, nature_path,
        character_position, character_scale,
        nature_opacity, output_size
    )

    # Sauvegarder
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[ASSEMBLE] Visuel final: {output_path}")

    return output_path


def assemble_batch(
    forge_root: str,
    scenes: list[dict],
    output_dir: str = "./assembled"
) -> list[str]:
    """
    Assemble plusieurs visuels en batch.
    Chaque scène est un dict avec les IDs d'actifs.
    
    Exemple:
    [
        {"background_id": "bg_001", "character_id": "char_003", "output": "scene_01.png"},
        {"background_id": "bg_005", "character_id": "char_001", "nature_id": "nat_002", "output": "scene_02.png"},
    ]
    """
    results = []
    for scene in scenes:
        output_path = os.path.join(output_dir, scene.get("output", f"scene_{len(results)+1:03d}.png"))
        try:
            path = assemble_single(
                forge_root=forge_root,
                background_id=scene["background_id"],
                character_id=scene.get("character_id"),
                nature_id=scene.get("nature_id"),
                output_path=output_path,
                character_position=scene.get("character_position", ("center", "bottom")),
                character_scale=scene.get("character_scale", 1.0),
                nature_opacity=scene.get("nature_opacity", 0.8),
                output_size=scene.get("output_size", (1920, 1080))
            )
            results.append(path)
        except Exception as e:
            print(f"[ASSEMBLE] ÉCHEC scène: {e}")
            results.append(None)

    return results


def deploy_to_mode(assembled_dir: str, mode_shared_images: str) -> int:
    """
    Copie les visuels assemblés vers {mode}/SHARED/IN/images/.
    """
    import shutil

    os.makedirs(mode_shared_images, exist_ok=True)
    count = 0

    for filepath in sorted(Path(assembled_dir).glob("*.png")):
        dest = os.path.join(mode_shared_images, filepath.name)
        shutil.copy2(filepath, dest)
        count += 1
        print(f"[ASSEMBLE] Déployé: {filepath.name} → {mode_shared_images}")

    print(f"[ASSEMBLE] {count} visuels déployés vers {mode_shared_images}")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F00 ASSEMBLE — Composite visuels finaux")
    parser.add_argument("--forge-root", default=".", help="Racine F00_ASSET_FORGE")
    parser.add_argument("--background", required=True, help="ID du background (ex: bg_001)")
    parser.add_argument("--character", default=None, help="ID du personnage (ex: char_003)")
    parser.add_argument("--nature", default=None, help="ID élément nature (ex: nat_002)")
    parser.add_argument("--output", default="./assembled/scene_001.png", help="Chemin de sortie")
    parser.add_argument("--deploy", default=None, help="Dossier SHARED/IN/images/ pour déployer")
    args = parser.parse_args()

    output = assemble_single(
        forge_root=args.forge_root,
        background_id=args.background,
        character_id=args.character,
        nature_id=args.nature,
        output_path=args.output
    )

    if args.deploy:
        deploy_to_mode(os.path.dirname(output), args.deploy)
