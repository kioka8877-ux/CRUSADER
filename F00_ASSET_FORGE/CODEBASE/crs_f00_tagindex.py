#!/usr/bin/env python3
"""
CRS F00 — TAG INDEX
Prend le JSON produit par l'oracle (Claude vision) après analyse de la toile,
et met à jour index.json avec les tags + crée/maintient le tag_index (reverse-index).

Usage:
  python crs_f00_tagindex.py --tags oracle_tags.json --manifest canvas_manifest.json --index ../index.json

Le fichier oracle_tags.json est le JSON produit par l'oracle quand il regarde la toile.
Le fichier canvas_manifest.json est produit par crs_f00_canvas.py (mapping numéro → fichier).
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def save_json(data: dict, path: str):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[TAGINDEX] Sauvegardé: {path}")


def apply_tags_to_index(
    index: dict,
    oracle_tags: dict,
    manifest: dict,
    bank: str = None,
    category: str = None,
    subcategory: str = None
) -> dict:
    """
    Applique les tags de l'oracle aux actifs dans index.json.
    
    Args:
        index: index.json chargé
        oracle_tags: JSON de l'oracle ({"1": {"visual": ..., "narrative": [...], "usage": [...]}, ...})
        manifest: manifest de la toile (mapping numéro → chemin fichier)
        bank: nom de la banque (ex: "BANK_B_NATURE")
        category: catégorie (ex: "nature")
        subcategory: sous-catégorie (ex: "fire")
    """
    # Déterminer la clé de catégorie dans index.json
    cat_key = category or "nature"  # défaut
    
    # Récupérer la liste des assets de cette catégorie
    assets = index.get(cat_key, [])
    
    # Créer un lookup par nom de fichier
    file_to_asset = {}
    for asset in assets:
        file_to_asset[asset.get("filename", "")] = asset
    
    # Le manifest peut être pour frames ou gifs
    # Structure: {"frames": {"mapping": {"1": "/path/to/frame_000001.png"}}, "gifs": {"mapping": {"1": "/path/to/gif_0001.gif"}}}
    
    updated_count = 0
    
    for canvas_type in ["frames", "gifs"]:
        mapping = manifest.get(canvas_type, {}).get("mapping", {})
        if not mapping:
            continue
        
        for num, filepath in mapping.items():
            # Le numéro dans l'oracle correspond au numéro dans le manifest
            if num not in oracle_tags:
                continue
            
            tags = oracle_tags[num]
            filename = os.path.basename(filepath)
            
            # Trouver l'asset correspondant dans index.json
            asset = file_to_asset.get(filename)
            if not asset:
                print(f"[TAGINDEX] Asset non trouvé dans index: {filename}")
                continue
            
            # Appliquer les tags
            asset["visual_description"] = tags.get("visual", "")
            asset["narrative_tags"] = tags.get("narrative", [])
            asset["usage_tags"] = tags.get("usage", [])
            asset["tagged_at"] = datetime.now(timezone.utc).isoformat()
            asset["tagged_by"] = "oracle"
            
            updated_count += 1
            print(f"[TAGINDEX] {asset['id']}: {tags.get('visual', '')[:50]}")
    
    print(f"[TAGINDEX] {updated_count} assets taggés")
    return index


def build_tag_index(index: dict) -> dict:
    """
    Construit/maintient le tag_index (reverse-index) à partir d'index.json.
    tag_index = {"rain": ["nat_001", "nat_051"], "danger": ["nat_001", ...], ...}
    """
    tag_index = {}
    
    # Parcourir toutes les catégories
    for cat_key in ["characters", "nature", "backgrounds", "clips"]:
        assets = index.get(cat_key, [])
        for asset in assets:
            asset_id = asset.get("id", "")
            
            # Collecter tous les tags de cet asset
            all_tags = []
            all_tags.extend(asset.get("auto_tags", []))
            all_tags.extend(asset.get("narrative_tags", []))
            all_tags.extend(asset.get("usage_tags", []))
            
            # Aussi indexer la description visuelle comme mots-clés
            visual = asset.get("visual_description", "")
            if visual:
                # Split en mots simples (pour recherche textuelle)
                visual_words = [w.lower().strip(".,;:!?") for w in visual.split() if len(w) > 2]
                all_tags.extend(visual_words)
            
            # Ajouter au reverse-index
            for tag in all_tags:
                tag_lower = tag.lower().strip()
                if not tag_lower:
                    continue
                if tag_lower not in tag_index:
                    tag_index[tag_lower] = []
                if asset_id not in tag_index[tag_lower]:
                    tag_index[tag_lower].append(asset_id)
    
    return tag_index


def search_assets(index: dict, tag_index: dict, query: str, limit: int = 20) -> list[dict]:
    """
    Recherche des assets par tag ou mot-clé.
    """
    query_lower = query.lower().strip()
    
    # Matching exact sur le tag_index
    matching_ids = set()
    
    for tag, ids in tag_index.items():
        if query_lower in tag:
            matching_ids.update(ids)
    
    # Récupérer les assets correspondants
    results = []
    for cat_key in ["characters", "nature", "backgrounds", "clips"]:
        for asset in index.get(cat_key, []):
            if asset.get("id") in matching_ids:
                results.append({
                    "id": asset["id"],
                    "file": asset["file"],
                    "category": asset.get("category", cat_key),
                    "visual": asset.get("visual_description", ""),
                    "narrative_tags": asset.get("narrative_tags", []),
                    "usage_tags": asset.get("usage_tags", [])
                })
                if len(results) >= limit:
                    break
    
    return results


def process_oracle_tags(
    tags_path: str,
    manifest_path: str,
    index_path: str,
    bank: str = None,
    category: str = None,
    subcategory: str = None
):
    """
    Pipeline complet : charge les tags de l'oracle, les applique à index.json,
    et reconstruit le tag_index.
    """
    # 1. Charger les fichiers
    print(f"[TAGINDEX] Chargement tags: {tags_path}")
    oracle_tags = load_json(tags_path)
    
    print(f"[TAGINDEX] Chargement manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    
    print(f"[TAGINDEX] Chargement index: {index_path}")
    index = load_json(index_path)
    
    # 2. Appliquer les tags
    print(f"\n[TAGINDEX] Application des tags...")
    index = apply_tags_to_index(index, oracle_tags, manifest, bank, category, subcategory)
    
    # 3. Reconstruire le tag_index
    print(f"\n[TAGINDEX] Construction du tag_index...")
    tag_index = build_tag_index(index)
    index["tag_index"] = tag_index
    index["last_tagged"] = datetime.now(timezone.utc).isoformat()
    
    # Stats
    print(f"\n[TAGINDEX] Tags indexés: {len(tag_index)}")
    top_tags = sorted(tag_index.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print(f"[TAGINDEX] Top 10 tags:")
    for tag, ids in top_tags:
        print(f"  {tag}: {len(ids)} assets")
    
    # 4. Sauvegarder
    save_json(index, index_path)
    
    return index


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="F00 TAG INDEX — Apply oracle vision tags to index.json")
    parser.add_argument("--tags", required=True, help="JSON produit par l'oracle (tags par numéro)")
    parser.add_argument("--manifest", required=True, help="Manifest de la toile (mapping numéro → fichier)")
    parser.add_argument("--index", default="../index.json", help="Chemin vers index.json")
    parser.add_argument("--bank", default=None, help="Banque (ex: BANK_B_NATURE)")
    parser.add_argument("--category", default=None, help="Catégorie (ex: nature)")
    parser.add_argument("--subcategory", default=None, help="Sous-catégorie (ex: fire)")
    parser.add_argument("--search", default=None, help="Rechercher des assets par tag (mode recherche)")
    args = parser.parse_args()

    if args.search:
        # Mode recherche
        index = load_json(args.index)
        tag_index = index.get("tag_index", {})
        results = search_assets(index, tag_index, args.search)
        print(f"\n[SEARCH] '{args.search}' → {len(results)} résultat(s):")
        for r in results:
            print(f"  {r['id']}: {r['file']} | {r['visual'][:60]}")
    else:
        # Mode tagging
        process_oracle_tags(args.tags, args.manifest, args.index, args.bank, args.category, args.subcategory)
