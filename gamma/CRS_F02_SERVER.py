"""
CRS_F02_SERVER.py — Serveur F02 CASTELLAN (stdlib uniquement)
=============================================================
Remplace Flask. Zéro dépendance externe.
Sert le viewer HTML + assets depuis IN/.
Accepte POST /api/save → écrit roadmap.json → shutdown automatique.

Usage:
    python CRS_F02_SERVER.py --input /path/IN/ --output /path/OUT/ [--port 8080]
"""

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR    = Path(__file__).parent.resolve()
DEFAULT_VIEWER = SCRIPT_DIR / "F02_CASTELLAN" / "CODEBASE" / "crs_f02_viewer.html"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

REQUIRED_META_KEYS  = {"fps", "format", "width", "height", "source_timing"}
REQUIRED_STYLE_KEYS = {
    "font_primary", "font_accent", "subtitle_size", "subtitle_position",
    "subtitle_color", "accent_color", "background_color",
    "grain_intensity", "vignette",
}
FORMATS = {
    "vertical":   {"width": 1080, "height": 1920},
    "horizontal": {"width": 1920, "height": 1080},
}


def make_handler(input_dir, output_dir, viewer_path, shutdown_event):
    timing_path  = Path(input_dir)  / "timing.json"
    images_dir   = Path(input_dir)  / "images"
    roadmap_path = Path(output_dir) / "roadmap.json"
    viewer_path  = Path(viewer_path)

    class Handler(BaseHTTPRequestHandler):

        def log_message(self, fmt, *args):
            pass

        def send_json(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def send_bytes(self, data, content_type):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(data))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path.rstrip("/") or "/"

            if path in ("/", "/index.html"):
                if not viewer_path.exists():
                    self.send_json({"error": f"Viewer introuvable : {viewer_path}"}, 404)
                    return
                self.send_bytes(viewer_path.read_bytes(), "text/html; charset=utf-8")

            elif path == "/api/timing":
                if not timing_path.exists():
                    self.send_json({"error": "timing.json introuvable"}, 404)
                    return
                with open(timing_path, encoding="utf-8") as f:
                    self.send_json(json.load(f))

            elif path == "/api/images":
                if not images_dir.is_dir():
                    self.send_json({"images": [], "count": 0})
                    return
                files = sorted(
                    p.name for p in images_dir.iterdir()
                    if p.suffix.lower() in IMAGE_EXTENSIONS
                )
                self.send_json({"images": files, "count": len(files)})

            elif path.startswith("/api/image/"):
                fname = Path(path[len("/api/image/"):]).name
                fpath = images_dir / fname
                if not fpath.exists():
                    self.send_json({"error": "Image introuvable"}, 404)
                    return
                ct = {
                    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".webp": "image/webp", ".gif": "image/gif",
                }.get(fpath.suffix.lower(), "image/png")
                self.send_bytes(fpath.read_bytes(), ct)

            elif path == "/api/status":
                img_count = len(list(images_dir.iterdir())) if images_dir.is_dir() else 0
                self.send_json({
                    "frigate":      "F02_CASTELLAN",
                    "timing_ready": timing_path.exists(),
                    "images_count": img_count,
                    "roadmap_saved": roadmap_path.exists(),
                })

            else:
                self.send_json({"error": "Route inconnue"}, 404)

        def do_POST(self):
            path = urlparse(self.path).path

            if path != "/api/save":
                self.send_json({"error": "Route inconnue"}, 404)
                return

            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)

            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self.send_json({"error": "JSON invalide"}, 400)
                return

            # Validation surface
            missing_top = [k for k in ["meta", "style", "timeline", "validated_by_magos"]
                           if k not in payload]
            if missing_top:
                self.send_json({"error": f"Clés manquantes : {missing_top}"}, 400)
                return

            if not payload.get("validated_by_magos"):
                self.send_json({"error": "validated_by_magos doit être true"}, 400)
                return

            meta         = payload.get("meta", {})
            missing_meta = REQUIRED_META_KEYS - set(meta.keys())
            if missing_meta:
                self.send_json({"error": f"meta : clés manquantes : {sorted(missing_meta)}"}, 400)
                return

            if meta.get("format") not in FORMATS:
                self.send_json({"error": f"meta.format invalide : '{meta.get('format')}'"}, 400)
                return

            style         = payload.get("style", {})
            missing_style = REQUIRED_STYLE_KEYS - set(style.keys())
            if missing_style:
                self.send_json({"error": f"style : clés manquantes : {sorted(missing_style)}"}, 400)
                return

            # Écrire roadmap.json
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            with open(roadmap_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            n = len(payload.get("timeline", []))
            print(f"\n[F02] ✅ roadmap.json sauvegardée — {n} slots validés.")
            self.send_json({"status": "ok", "timeline_count": n})

            # Shutdown après réponse
            threading.Thread(target=shutdown_event.set, daemon=True).start()

    return Handler


def main():
    parser = argparse.ArgumentParser(description="CRS_F02_SERVER — Viewer F02 (stdlib, zero pip)")
    parser.add_argument("--input",  required=True, help="Dossier IN/ (timing.json + images/)")
    parser.add_argument("--output", required=True, help="Dossier OUT/ (recevra roadmap.json)")
    parser.add_argument("--viewer", default=None,  help="Chemin vers crs_f02_viewer.html")
    parser.add_argument("--port",   type=int, default=8080)
    args = parser.parse_args()

    viewer = args.viewer or str(DEFAULT_VIEWER)
    if not Path(viewer).exists():
        print(f"[ERREUR] Viewer HTML introuvable : {viewer}")
        sys.exit(1)

    shutdown_event = threading.Event()
    handler        = make_handler(args.input, args.output, viewer, shutdown_event)
    server         = HTTPServer(("0.0.0.0", args.port), handler)

    print(f"\n[F02] Serveur démarré sur port {args.port}")
    print(f"[F02] Viewer : validez roadmap.json dans le navigateur")
    print(f"[F02] Shutdown automatique après validation.\n")

    server_thread        = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    shutdown_event.wait()
    print("[F02] Shutdown.")
    server.shutdown()


if __name__ == "__main__":
    main()
