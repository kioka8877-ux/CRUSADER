#!/usr/bin/env python3
"""
CRS F00 — PROCESS
Traite les frames extraites :
  - Rembg : détourage IA pour personnages/objets → PNG transparent
  - Chroma key : détourage feu/fumée sur fond noir → PNG/GIF transparent
  - Aucun traitement : décors purs → PNG direct (déjà prêt)

Détection automatique du type de traitement selon le mode demandé.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from PIL import Image
import io

# Rembg — import conditionnel (installé sur le runner GitHub Actions)
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("[PROCESS] WARNING: rembg non installé — mode Rembg désactivé")


def process_with_rembg(input_path: str, output_path: str, session=None) -> bool:
    """
    Détoure une image avec Rembg → PNG transparent.
    """
    if not REMBG_AVAILABLE:
        print(f"[PROCESS] Rembg non disponible, skip: {input_path}")
        return False

    try:
        with open(input_path, "rb") as f:
            input_data = f.read()

        if session:
            output_data = remove(input_data, session=session)
        else:
            output_data = remove(input_data)

        with open(output_path, "wb") as f:
            f.write(output_data)

        return True
    except Exception as e:
        print(f"[PROCESS] Rembg erreur {input_path}: {e}")
        return False


def process_with_chroma_key(input_path: str, output_path: str,
                            threshold: int = 30) -> bool:
    """
    Détoure sur fond noir : rend les pixels noirs transparents.
    Utilise Pillow pour un contrôle précis du seuil.
    """
    try:
        img = Image.open(input_path).convert("RGBA")
        pixels = img.load()
        width, height = img.size

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                # Si pixel proche du noir → transparent
                if r < threshold and g < threshold and b < threshold:
                    pixels[x, y] = (0, 0, 0, 0)

        img.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"[PROCESS] Chroma key erreur {input_path}: {e}")
        return False


def process_gif_chroma_key(input_path: str, output_path: str,
                           threshold: int = 30) -> bool:
    """
    Détoure un GIF sur fond noir frame par frame.
    """
    try:
        gif = Image.open(input_path)
        frames = []
        durations = []

        frame_num = 0
        while True:
            try:
                frame = gif.convert("RGBA")
                pixels = frame.load()
                width, height = frame.size

                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[x, y]
                        if r < threshold and g < threshold and b < threshold:
                            pixels[x, y] = (0, 0, 0, 0)

                frames.append(frame)
                durations.append(gif.info.get("duration", 100))

                frame_num += 1
                gif.seek(gif.tell() + 1)
            except EOFError:
                break

        if frames:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                disposal=2
            )
            return True
        return False
    except Exception as e:
        print(f"[PROCESS] GIF chroma key erreur {input_path}: {e}")
        return False


def classify_frame(image_path: str) -> str:
    """
    Classifie une frame : 'character', 'nature_dark_bg', 'background'.
    Heuristique simple basée sur la luminosité et la distribution.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        # Resize pour accélérer
        img_small = img.resize((100, 100))
        pixels = list(img_small.getdata())

        # Calculer luminosité moyenne
        total_brightness = sum((r + g + b) / 3 for r, g, b in pixels)
        avg_brightness = total_brightness / len(pixels)

        # Si très sombre → probablement fond noir (feu/fumée sur noir)
        if avg_brightness < 30:
            return "nature_dark_bg"

        # Si très lumineux et uniforme → probablement décor
        # (heuristique simplifiée — MediaPipe pourrait affiner)
        return "background"

    except Exception as e:
        print(f"[PROCESS] Classification erreur {image_path}: {e}")
        return "background"


def process_frames(frames: list[str], mode: str, output_dir: str) -> list[dict]:
    """
    Traite une liste de frames selon le mode.
    mode: 'characters' | 'nature' | 'backgrounds' | 'all'
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    session = None

    if mode in ("characters", "all") and REMBG_AVAILABLE:
        session = new_session("u2net")

    for i, frame_path in enumerate(frames):
        filename = Path(frame_path).stem + ".png"
        output_path = os.path.join(output_dir, filename)

        # Déterminer le traitement
        if mode == "characters":
            success = process_with_rembg(frame_path, output_path, session)
            asset_type = "character"
        elif mode == "nature":
            # Chroma key pour feu/fumée sur fond noir
            success = process_with_chroma_key(frame_path, output_path)
            asset_type = "nature"
        elif mode == "backgrounds":
            # Copie directe, pas de traitement
            import shutil
            shutil.copy2(frame_path, output_path)
            success = True
            asset_type = "background"
        elif mode == "all":
            # Auto-classification
            frame_type = classify_frame(frame_path)
            if frame_type == "nature_dark_bg":
                success = process_with_chroma_key(frame_path, output_path)
                asset_type = "nature"
            elif frame_type == "character" and REMBG_AVAILABLE:
                success = process_with_rembg(frame_path, output_path, session)
                asset_type = "character"
            else:
                import shutil
                shutil.copy2(frame_path, output_path)
                success = True
                asset_type = "background"
        else:
            print(f"[PROCESS] Mode inconnu: {mode}")
            break

        if success:
            results.append({
                "input": frame_path,
                "output": output_path,
                "type": asset_type,
                "status": "ok"
            })
            print(f"[PROCESS] {i+1}/{len(frames)} → {filename} ({asset_type})")
        else:
            results.append({
                "input": frame_path,
                "output": None,
                "type": asset_type,
                "status": "error"
            })

    return results


def process_gifs(gifs: list[str], mode: str, output_dir: str) -> list[dict]:
    """
    Traite les GIFs (chroma key si nature, copie sinon).
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for gif_path in gifs:
        filename = Path(gif_path).name
        output_path = os.path.join(output_dir, filename)

        if mode in ("nature", "all"):
            success = process_gif_chroma_key(gif_path, output_path)
        else:
            import shutil
            shutil.copy2(gif_path, output_path)
            success = True

        results.append({
            "input": gif_path,
            "output": output_path if success else None,
            "type": "nature" if mode in ("nature", "all") else "gif",
            "status": "ok" if success else "error"
        })

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="F00 PROCESS — Rembg + chroma key")
    parser.add_argument("--frames", help="Dossier contenant les frames à traiter")
    parser.add_argument("--gifs", help="Dossier contenant les GIFs à traiter")
    parser.add_argument("--output", default="./processed", help="Dossier de sortie")
    parser.add_argument("--mode", default="all", choices=["characters", "nature", "backgrounds", "all"])
    args = parser.parse_args()

    all_results = []

    if args.frames:
        frame_list = sorted(str(f) for f in Path(args.frames).glob("*.png"))
        results = process_frames(frame_list, args.mode, os.path.join(args.output, "frames"))
        all_results.extend(results)

    if args.gifs:
        gif_list = sorted(str(f) for f in Path(args.gifs).glob("*.gif"))
        results = process_gifs(gif_list, args.mode, os.path.join(args.output, "gifs"))
        all_results.extend(results)

    ok_count = len([r for r in all_results if r["status"] == "ok"])
    err_count = len([r for r in all_results if r["status"] == "error"])
    print(f"\n[PROCESS] Terminé: {ok_count} réussis, {err_count} échoués")
    print(json.dumps(all_results, indent=2))
