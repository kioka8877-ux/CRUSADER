#!/usr/bin/env python3
"""
CRUSADER Delta — F03A L'INTERPRÉTEUR
crs_f03a_interpreteur.py

L'Oracle reçoit des références de style visuel et un storyboard,
puis produit les fichiers Canvas paramétriques :
  - characters.js   (personnage articulé avec émotions)
  - backgrounds.js  (décors vivants qui respirent)
  - effects.js      (particules, vignette, texte)

Pour Phase 3, les fichiers sont pré-écrits (templates).
En production, l'Oracle analysera les captures de style pour
adapter la palette, les proportions et le style graphique.

Usage:
  python crs_f03a_interpreteur.py --storyboard <path> --style-refs <dir> --output <dir>
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone, timedelta


def log(msg):
    tz = timezone(timedelta(hours=1))
    ts = datetime.now(tz).strftime("%H:%M:%S")
    print(f"[F03A {ts}] {msg}")


def interpret_style(style_refs_dir):
    """
    Phase 3: Returns default style tokens.
    Future: Will analyze screenshots and extract style parameters.
    """
    tokens = {
        "palette": {
            "skin": "#F4C280",
            "outline": "#2C3E50",
            "hair": "#34495E",
            "shirt": "#3498DB",
            "pants": "#2C3E50",
            "shoes": "#1A1A2E",
            "eye": "#FFFFFF",
            "pupil": "#2C3E50",
            "mouth": "#C0392B",
        },
        "character": {
            "scale": 2.5,
            "line_width": 3,
            "style": "stickman_plus",  # stickman_plus | cartoon | realistic
        },
        "animation": {
            "fps": 30,
            "squash_intensity": 0.08,
            "breathing_speed": 1.5,
            "walk_speed": 3,
        },
        "backgrounds": {
            "available": ["nature", "city", "office", "abstract"],
            "default": "nature",
        },
        "effects": {
            "vignette_intensity": 0.35,
            "particles_enabled": True,
        },
    }

    if style_refs_dir and os.path.isdir(style_refs_dir):
        refs = [f for f in os.listdir(style_refs_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        log(f"Found {len(refs)} style reference(s) in {style_refs_dir}")
        # Future: Analyze images to extract palette, proportions, style
    else:
        log("No style references provided — using default tokens")

    return tokens


def generate_output(storyboard_path, style_tokens, output_dir):
    """
    Copy the template JS files to the output directory.
    In production, these would be dynamically generated based on style_tokens.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Source directory (same dir as this script)
    src_dir = os.path.dirname(os.path.abspath(__file__))

    # Copy JS files
    for filename in ["characters.js", "backgrounds.js", "effects.js"]:
        src = os.path.join(src_dir, filename)
        dst = os.path.join(output_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            log(f"✅ Generated {filename} → {dst}")
        else:
            log(f"❌ Template not found: {src}")
            sys.exit(1)

    # Save style tokens
    tokens_path = os.path.join(output_dir, "style_tokens.json")
    with open(tokens_path, "w") as f:
        json.dump(style_tokens, f, indent=2, ensure_ascii=False)
    log(f"✅ Generated style_tokens.json → {tokens_path}")

    # Generate manifest
    manifest = {
        "generated_at": datetime.now(timezone(timedelta(hours=1))).isoformat(),
        "engine": "VibeForge (Canvas 2D)",
        "phase": "3",
        "files": ["characters.js", "backgrounds.js", "effects.js", "style_tokens.json"],
        "style_tokens": style_tokens,
    }
    manifest_path = os.path.join(output_dir, "f03a_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    log(f"✅ Generated f03a_manifest.json → {manifest_path}")

    return manifest


def main():
    parser = argparse.ArgumentParser(description="F03A L'Interpréteur — CRUSADER Delta")
    parser.add_argument("--storyboard", help="Path to storyboard.json from F02")
    parser.add_argument("--style-refs", help="Directory with style reference images")
    parser.add_argument("--output", default="../OUT", help="Output directory for generated files")
    args = parser.parse_args()

    log("═══════════════════════════════════════════")
    log("   F03A L'INTERPRÉTEUR — CRUSADER Delta   ")
    log("   Engine: VibeForge (Canvas 2D)          ")
    log("═══════════════════════════════════════════")

    # Step 1: Interpret style
    log("Step 1: Analyzing style references...")
    style_tokens = interpret_style(args.style_refs)
    log(f"  Palette: {style_tokens['palette']['shirt']} shirt, {style_tokens['palette']['skin']} skin")
    log(f"  Scale: {style_tokens['character']['scale']}x")
    log(f"  Style: {style_tokens['character']['style']}")

    # Step 2: Generate output files
    log("Step 2: Generating Canvas parametric files...")
    manifest = generate_output(args.storyboard, style_tokens, args.output)

    log("═══════════════════════════════════════════")
    log(f"  ✅ F03A COMPLETE — {len(manifest['files'])} files generated")
    log("═══════════════════════════════════════════")


if __name__ == "__main__":
    main()
