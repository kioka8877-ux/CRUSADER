#!/usr/bin/env python3
"""
CRS F00 — INDEX
Met à jour index.json avec les nouveaux actifs traités.
Parcourt les BANK_*/ et enregistre chaque fichier avec ses métadonnées.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image


# Mapping banque → catégorie index.json
BANK_MAPPING = {
    "BANK_A_CHARACTERS": "characters",
    "BANK_B_NATURE": "nature",
    "BANK_C_BACKGROUNDS": "backgrounds",
    "BANK_D_CLIPS": "clips",
}

# Sous-catégories par banque
SUBCATEGORIES = {
    "BANK_A_CHARACTERS": ["standing", "sitting", "walking", "pointing", "idle", "gesture"],
    "BANK_B_NATURE": ["fire", "space", "weather", "water", "smoke"],
    "BANK_C_BACKGROUNDS": ["indoor", "outdoor", "abstract", "cityscape"],
    "BANK_D_CLIPS": [],
}


def get_file_hash(filepath: str) -> str:
    """Hash MD5 du fichier pour détecter les doublons."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def get_image_metadata(filepath: str) -> dict:
    """Métadonnées d'une image (dimensions, transparence)."""
    try:
        img = Image.open(filepath)
        width, height = img.size
        has_transparency = img.mode in ("RGBA", "LA") or "transparency" in img.info
        return {
            "width": width,
            "height": height,
            "has_transparency": has_transparency
        }
    except Exception:
        return {"width": None, "height": None, "has_transparency": False}


def generate_asset_id(category: str, existing_ids: set) -> str:
    """Génère un ID unique pour un actif."""
    prefixes = {
        "characters": "char",
        "nature": "nat",
        "backgrounds": "bg",
        "clips": "clip"
    }
    prefix = prefixes.get(category, "asset")
    num = 1
    while f"{prefix}_{num:03d}" in existing_ids:
        num += 1
    return f"{prefix}_{num:03d}"


def scan_bank(bank_dir: str, category: str, existing_assets: list[dict]) -> list[dict]:
    """
    Parcourt une banque et enregistre tous les fichiers.
    Évite les doublons (par hash).
    """
    new_assets = []
    existing_hashes = {a.get("file_hash") for a in existing_assets}
    existing_ids = {a.get("id") for a in existing_assets}

    if not os.path.exists(bank_dir):
        return new_assets

    # Parcourir récursivement
    for root, dirs, files in os.walk(bank_dir):
        for filename in sorted(files):
            if filename.startswith(".") or filename in ("index.json", "README.md", ".gitkeep"):
                continue

            filepath = os.path.join(root, filename)
            file_hash = get_file_hash(filepath)

            # Skip si déjà indexé
            if file_hash in existing_hashes:
                continue

            # Déterminer la sous-catégorie
            rel_path = os.path.relpath(filepath, bank_dir)
            subcategory = rel_path.split(os.sep)[0] if os.sep in rel_path else "root"

            # Métadonnées
            asset_id = generate_asset_id(category, existing_ids)
            existing_ids.add(asset_id)

            asset = {
                "id": asset_id,
                "file": os.path.relpath(filepath, os.path.dirname(bank_dir)),
                "filename": filename,
                "category": category,
                "subcategory": subcategory if subcategory != "root" else None,
                "file_hash": file_hash,
                "size_bytes": os.path.getsize(filepath),
                "indexed_at": datetime.now(timezone.utc).isoformat()
            }

            # Métadonnées image si PNG/GIF
            if filename.lower().endswith((".png", ".gif")):
                asset.update(get_image_metadata(filepath))

            # Métadonnées vidéo si MP4
            if filename.lower().endswith(".mp4"):
                asset["format"] = "mp4"

            new_assets.append(asset)
            print(f"[INDEX] {asset_id}: {rel_path}")

    return new_assets


def update_index(index_path: str, forge_root: str) -> dict:
    """
    Met à jour index.json en parcourant toutes les banques.
    """
    # Charger l'index existant
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            index = json.load(f)
    else:
        index = {
            "version": "1.0",
            "characters": [],
            "nature": [],
            "backgrounds": [],
            "clips": []
        }

    total_new = 0

    for bank_name, category in BANK_MAPPING.items():
        bank_dir = os.path.join(forge_root, bank_name)
        existing = index.get(category, [])
        new_assets = scan_bank(bank_dir, category, existing)

        if new_assets:
            index[category] = existing + new_assets
            total_new += len(new_assets)
            print(f"[INDEX] {bank_name}: {len(new_assets)} nouveaux actifs")

    # Mettre à jour le timestamp
    index["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Sauvegarder
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n[INDEX] Total nouveaux actifs: {total_new}")
    print(f"[INDEX] Index mis à jour: {index_path}")

    # Stats
    for category in ["characters", "nature", "backgrounds", "clips"]:
        count = len(index.get(category, []))
        print(f"  {category}: {count} actifs")

    return index


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="F00 INDEX — Update index.json")
    parser.add_argument("--forge-root", default=".", help="Racine de F00_ASSET_FORGE")
    parser.add_argument("--index", default=None, help="Chemin vers index.json (défaut: {forge_root}/index.json)")
    args = parser.parse_args()

    index_path = args.index or os.path.join(args.forge_root, "index.json")
    update_index(index_path, args.forge_root)
