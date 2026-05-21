"""
crs_f02_castellan.py — Frégate F02 CASTELLAN
=============================================
Serveur Flask REST + viewer HTML interactif pour la configuration créative.
Lit timing.json + images/ depuis IN/, produit roadmap.json dans OUT/
via validation opérateur dans le navigateur.

Usage:
    python crs_f02_castellan.py --input /path/to/IN/ --output /path/to/OUT/ \\
                                 [--viewer /path/to/crs_f02_viewer.html] [--port 5002]

Dépendances (installées dans le notebook) :
    flask >= 2.0
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ─── Constantes ───────────────────────────────────────────────────────────────

DEFAULT_PORT     = 5002
TIMING_FILENAME  = "timing.json"
ROADMAP_FILENAME = "roadmap.json"
IMAGES_SUBDIR    = "images"
VIEWER_FILENAME  = "crs_f02_viewer.html"

FORMATS = {
    "vertical":   {"width": 1080, "height": 1920},
    "horizontal": {"width": 1920, "height": 1080},
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# ─── Flask app ────────────────────────────────────────────────────────────────

def create_app(input_dir: str, output_dir: str, viewer_path: str):
    try:
        from flask import Flask, jsonify, request, send_file, abort
    except ImportError:
        print("[ERREUR] Flask non installé. Lancez : pip install flask")
        sys.exit(1)

    app = Flask(__name__)

    timing_path  = os.path.join(input_dir, TIMING_FILENAME)
    images_dir   = os.path.join(input_dir, IMAGES_SUBDIR)
    roadmap_path = os.path.join(output_dir, ROADMAP_FILENAME)

    # ── Routes ────────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        if not os.path.isfile(viewer_path):
            abort(404, description=f"Viewer introuvable : {viewer_path}")
        return send_file(viewer_path)

    @app.route("/api/timing")
    def api_timing():
        if not os.path.isfile(timing_path):
            return jsonify({"error": f"timing.json introuvable : {timing_path}"}), 404
        with open(timing_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)

    @app.route("/api/images")
    def api_images():
        if not os.path.isdir(images_dir):
            return jsonify({"images": [], "warning": f"Dossier images introuvable : {images_dir}"})
        files = sorted([
            f for f in os.listdir(images_dir)
            if Path(f).suffix.lower() in IMAGE_EXTENSIONS
        ])
        return jsonify({"images": files, "count": len(files)})

    @app.route("/api/image/<path:filename>")
    def api_image(filename):
        safe_name = os.path.basename(filename)
        full_path = os.path.join(images_dir, safe_name)
        if not os.path.isfile(full_path):
            abort(404)
        return send_file(full_path)

    @app.route("/api/save", methods=["POST"])
    def api_save():
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "Payload JSON vide"}), 400

        required = ["meta", "style", "timeline", "validated_by_magos"]
        missing = [k for k in required if k not in payload]
        if missing:
            return jsonify({"error": f"Clés manquantes : {missing}"}), 400

        if not payload.get("validated_by_magos"):
            return jsonify({"error": "validated_by_magos doit être true"}), 400

        if not isinstance(payload.get("timeline"), list) or len(payload["timeline"]) == 0:
            return jsonify({"error": "timeline est vide"}), 400

        os.makedirs(output_dir, exist_ok=True)
        with open(roadmap_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(roadmap_path) / 1024
        print(f"[CASTELLAN] roadmap.json écrit → {roadmap_path} ({size_kb:.1f} KB)")
        return jsonify({"status": "ok", "path": roadmap_path, "size_kb": round(size_kb, 1)})

    @app.route("/api/status")
    def api_status():
        return jsonify({
            "frigate":        "F02_CASTELLAN",
            "timing_ready":   os.path.isfile(timing_path),
            "images_ready":   os.path.isdir(images_dir),
            "roadmap_exists": os.path.isfile(roadmap_path),
        })

    return app

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F02 CASTELLAN — Config créative + Viewer")
    parser.add_argument("--input",  required=True, help="Chemin vers le dossier IN/")
    parser.add_argument("--output", required=True, help="Chemin vers le dossier OUT/")
    parser.add_argument("--viewer", default=None,  help="Chemin vers crs_f02_viewer.html")
    parser.add_argument("--port",   type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    viewer_path = args.viewer
    if viewer_path is None:
        viewer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), VIEWER_FILENAME)

    print()
    print("═══════════════════════════════════════════")
    print("  F02 CASTELLAN — Lancement du serveur")
    print("═══════════════════════════════════════════")
    print(f"  IN     : {args.input}")
    print(f"  OUT    : {args.output}")
    print(f"  Viewer : {viewer_path}")
    print(f"  Port   : {args.port}")
    print()

    timing_path = os.path.join(args.input, TIMING_FILENAME)
    if not os.path.isfile(timing_path):
        print(f"[ATTENTION] timing.json introuvable : {timing_path}")
        print("            Démarrage quand même — /api/timing retournera une erreur.")

    if not os.path.isfile(viewer_path):
        print(f"[ERREUR] Viewer HTML introuvable : {viewer_path}")
        sys.exit(1)

    app = create_app(args.input, args.output, viewer_path)

    print(f"  Viewer disponible sur : http://localhost:{args.port}/")
    print("═══════════════════════════════════════════")
    print()

    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
