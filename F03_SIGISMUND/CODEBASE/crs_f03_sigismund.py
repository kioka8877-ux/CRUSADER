"""
crs_f03_sigismund.py — Frégate F03 SIGISMUND
=============================================
Prépare le projet Remotion (copie assets dans public/) et lance le rendu vidéo.
Remotion utilise headless Chrome — installer Node.js + Chrome avant de lancer.

Usage:
    python crs_f03_sigismund.py \\
        --input   /path/to/F03/IN/ \\
        --output  /path/to/F03/OUT/ \\
        --project /path/to/remotion_project/ \\
        [--composition CrusaderShort] \\
        [--gl swangle]

Dépendances système (installées dans le notebook) :
    Node.js >= 18, npm, google-chrome ou chromium-browser
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# ─── Constantes ───────────────────────────────────────────────────────────────

DEFAULT_COMPOSITION = "CrusaderShort"
DEFAULT_OUTPUT_FILE = "short_render.mp4"
REQUIRED_INPUTS = ["timing.json", "roadmap.json", "audio_clean.mp3"]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def run(cmd, cwd=None, check=True):
    """Lance une commande shell, affiche la sortie en temps réel."""
    print(f"[CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=isinstance(cmd, str),
        check=False,
    )
    if check and result.returncode != 0:
        print(f"[ERREUR] Exit code {result.returncode}")
        sys.exit(result.returncode)
    return result

def copy_assets(input_dir: str, public_dir: str):
    """Copie timing.json, roadmap.json, audio et images/ dans public/."""
    os.makedirs(public_dir, exist_ok=True)

    # Fichiers individuels
    for fname in REQUIRED_INPUTS:
        src = os.path.join(input_dir, fname)
        dst = os.path.join(public_dir, fname)
        if not os.path.isfile(src):
            print(f"[ERREUR] Fichier manquant : {src}")
            sys.exit(1)
        shutil.copy2(src, dst)
        size_kb = os.path.getsize(dst) / 1024
        print(f"[OK] {fname} copié → {dst} ({size_kb:.1f} KB)")

    # Dossier images/
    src_images = os.path.join(input_dir, "images")
    dst_images = os.path.join(public_dir, "images")
    if os.path.isdir(src_images):
        if os.path.exists(dst_images):
            shutil.rmtree(dst_images)
        shutil.copytree(src_images, dst_images)
        count = len(os.listdir(dst_images))
        print(f"[OK] images/ copié → {dst_images} ({count} fichier(s))")
    else:
        os.makedirs(dst_images, exist_ok=True)
        print(f"[ATTENTION] Dossier images/ absent dans IN/ — rendu sans images.")

def find_chrome():
    """Détecte l'exécutable Chrome disponible sur le système."""
    candidates = [
        "google-chrome",
        "google-chrome-stable",
        "chromium-browser",
        "chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
    ]
    for c in candidates:
        result = subprocess.run(["which", c], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    return None

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F03 SIGISMUND — Setup + Rendu Remotion")
    parser.add_argument("--input",       required=True, help="Chemin vers F03/IN/")
    parser.add_argument("--output",      required=True, help="Chemin vers F03/OUT/")
    parser.add_argument("--project",     required=True, help="Répertoire du projet Remotion")
    parser.add_argument("--composition", default=DEFAULT_COMPOSITION)
    parser.add_argument("--gl",          default="swangle",
                        help="Backend GL Remotion (swangle = logiciel, recommandé Colab)")
    args = parser.parse_args()

    output_file = os.path.join(args.output, DEFAULT_OUTPUT_FILE)
    public_dir  = os.path.join(args.project, "public")

    print()
    print("═══════════════════════════════════════════")
    print("  F03 SIGISMUND — Rendu Remotion")
    print("═══════════════════════════════════════════")
    print(f"  IN         : {args.input}")
    print(f"  OUT        : {args.output}")
    print(f"  Projet     : {args.project}")
    print(f"  Composition: {args.composition}")
    print(f"  GL backend : {args.gl}")
    print()

    # ── 1. Copie des assets dans public/ ────────────────────────────────────
    print("[SIGISMUND] Copie des assets vers public/...")
    copy_assets(args.input, public_dir)

    # ── 2. npm install (seulement si node_modules absent) ───────────────────
    node_modules = os.path.join(args.project, "node_modules")
    if not os.path.isdir(node_modules):
        print("\n[SIGISMUND] npm install...")
        run(["npm", "install", "--prefer-offline"], cwd=args.project)
    else:
        print("[SIGISMUND] node_modules existant — npm install ignoré.")

    # ── 3. Détection Chrome ──────────────────────────────────────────────────
    chrome_path = find_chrome()
    if chrome_path:
        print(f"[SIGISMUND] Chrome détecté : {chrome_path}")
    else:
        print("[ATTENTION] Chrome non détecté. Remotion utilisera sa découverte automatique.")

    # ── 4. Rendu Remotion ────────────────────────────────────────────────────
    os.makedirs(args.output, exist_ok=True)

    render_cmd = [
        "npx", "--yes", "remotion", "render",
        "src/index.jsx",
        args.composition,
        output_file,
        f"--gl={args.gl}",
    ]
    if chrome_path:
        render_cmd.append(f"--browser-executable={chrome_path}")

    print(f"\n[SIGISMUND] Lancement du rendu → {output_file}")
    run(render_cmd, cwd=args.project)

    # ── 5. Vérification sortie ───────────────────────────────────────────────
    if not os.path.isfile(output_file):
        print(f"[ERREUR] short_render.mp4 introuvable après rendu : {output_file}")
        sys.exit(1)

    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print()
    print("═══════════════════════════════════════════")
    print("  SIGISMUND — MISSION ACCOMPLIE")
    print(f"  {output_file}")
    print(f"  Taille : {size_mb:.1f} MB")
    print("═══════════════════════════════════════════")
    print()


if __name__ == "__main__":
    main()
