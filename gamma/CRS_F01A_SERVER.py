"""
CRS_F01A_SERVER.py — Serveur F01A local (stdlib pure, zéro pip)
Expose le viewer silences+vitesse sur port 5001.
Auto-shutdown après POST /api/validate.
"""
import http.server
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path

PORT = 5001
AUDIO_IN_PATH = None   # set at startup
OUT_DIR = None


def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return round(float(r.stdout.strip()), 4)
    except Exception:
        return 0.0


def detect_silences(path, threshold_db=-40.0, min_dur=0.5):
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", path,
         "-af", f"silencedetect=noise={threshold_db}dB:d={min_dur}",
         "-f", "null", "-"],
        capture_output=True, text=True
    )
    silences, cur_start = [], None
    for line in r.stderr.splitlines():
        if "silence_start" in line:
            try:
                cur_start = float(line.split("silence_start:")[1].strip())
            except Exception:
                pass
        elif "silence_end" in line and cur_start is not None:
            try:
                parts = line.split("silence_end:")[1].split("|")
                end = float(parts[0].strip())
                dur = float(parts[1].split(":")[1].strip()) if len(parts) > 1 else end - cur_start
                silences.append({"start": round(cur_start, 4), "end": round(end, 4), "duration": round(dur, 4)})
                cur_start = None
            except Exception:
                pass
    return silences


def get_waveform_peaks(path, n=300):
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp:
        raw = tmp.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", "8000", "-f", "f32le", raw],
            capture_output=True
        )
        data = open(raw, "rb").read()
        if not data:
            return [0.0] * n
        samples = struct.unpack(f"{len(data)//4}f", data)
        chunk = max(len(samples) // n, 1)
        peaks = [round(float(max(abs(v) for v in samples[i*chunk:i*chunk+chunk])), 4)
                 for i in range(n) if samples[i*chunk:i*chunk+chunk]]
        mx = max(peaks) if peaks else 1.0
        return [round(p/mx, 4) for p in peaks] if mx > 0 else peaks
    finally:
        if os.path.exists(raw):
            os.unlink(raw)


def apply_speed(input_path, output_path, speed):
    """Applique le changement de vitesse via FFmpeg atempo."""
    # atempo accepte 0.5-2.0, chaîner si hors plage
    if 0.5 <= speed <= 2.0:
        af = f"atempo={speed}"
    elif speed < 0.5:
        # deux passes : ex 0.3 = atempo=0.5,atempo=0.6
        af = f"atempo=0.5,atempo={round(speed/0.5, 4)}"
    else:
        # speed > 2.0 : ex 2.5 = atempo=2.0,atempo=1.25
        af = f"atempo=2.0,atempo={round(speed/2.0, 4)}"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-af", af,
         "-c:a", "libmp3lame", "-q:a", "2", output_path],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])


def build_audio_clean(input_path, out_dir, decision):
    """Produit audio_clean.mp3 selon la décision opérateur."""
    import shutil
    os.makedirs(out_dir, exist_ok=True)
    tmp_step = os.path.join(out_dir, "_tmp_step.mp3")
    final = os.path.join(out_dir, "audio_clean.mp3")

    remove = decision.get("remove_silences", False)
    speed  = float(decision.get("speed", 1.0))
    thr    = float(decision.get("threshold_db", -40.0))
    mind   = float(decision.get("min_duration", 0.5))

    if remove:
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-af", f"silenceremove=stop_periods=-1:stop_duration={mind}:stop_threshold={thr}dB",
             "-c:a", "libmp3lame", "-q:a", "2", tmp_step],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-600:])
        src = tmp_step
    else:
        src = input_path

    if abs(speed - 1.0) > 0.01:
        apply_speed(src, final, speed)
    else:
        shutil.copy2(src, final)

    if os.path.exists(tmp_step):
        os.unlink(tmp_step)
    return final


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[F01A] {fmt % args}")

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path, mime):
        data = open(path, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path
        qs     = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            viewer = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "F01_GRIMALDUS/F01A_CASTELLAN_AUDIO/CODEBASE/crs_f01a_viewer.html")
            if os.path.exists(viewer):
                self._serve_file(viewer, "text/html; charset=utf-8")
            else:
                self._json(404, {"error": "viewer HTML introuvable"})

        elif path == "/api/audio":
            if not AUDIO_IN_PATH or not os.path.exists(AUDIO_IN_PATH):
                self._json(404, {"error": "audio_raw.mp3 introuvable"})
                return
            self._serve_file(AUDIO_IN_PATH, "audio/mpeg")

        elif path == "/api/status":
            self._json(200, {
                "frigate": "F01A_CASTELLAN_AUDIO",
                "audio_in_ready": bool(AUDIO_IN_PATH and os.path.exists(AUDIO_IN_PATH)),
                "audio_in_path": AUDIO_IN_PATH,
            })

        elif path == "/api/waveform":
            if not AUDIO_IN_PATH or not os.path.exists(AUDIO_IN_PATH):
                self._json(404, {"error": "audio_raw.mp3 introuvable"}); return
            try:
                peaks = get_waveform_peaks(AUDIO_IN_PATH)
                dur   = ffprobe_duration(AUDIO_IN_PATH)
                self._json(200, {"peaks": peaks, "duration": dur, "samples": len(peaks)})
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif path == "/api/analyze":
            if not AUDIO_IN_PATH or not os.path.exists(AUDIO_IN_PATH):
                self._json(404, {"error": "audio_raw.mp3 introuvable"}); return
            try:
                thr  = float(qs.get("threshold_db", ["-40.0"])[0])
                mind = float(qs.get("min_duration",  ["0.5"])[0])
                dur  = ffprobe_duration(AUDIO_IN_PATH)
                sils = detect_silences(AUDIO_IN_PATH, thr, mind)
                total = round(sum(s["duration"] for s in sils), 4)
                self._json(200, {
                    "silences": sils,
                    "silence_count": len(sils),
                    "silence_total_seconds": total,
                    "original_duration": dur,
                    "duration_after_removal": round(max(dur - total, 0), 4),
                    "threshold_db": thr,
                    "min_duration": mind,
                })
            except Exception as e:
                self._json(500, {"error": str(e)})

        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/validate":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length) if length else b"{}"
            try:
                decision = json.loads(body)
            except Exception:
                self._json(400, {"error": "JSON invalide"}); return

            if not AUDIO_IN_PATH or not os.path.exists(AUDIO_IN_PATH):
                self._json(404, {"error": "audio_raw.mp3 introuvable"}); return

            try:
                # 1. Sauvegarder silence_decision.json dans OUT
                os.makedirs(OUT_DIR, exist_ok=True)
                decision_path = os.path.join(OUT_DIR, "silence_decision.json")
                with open(decision_path, "w", encoding="utf-8") as f:
                    json.dump(decision, f, ensure_ascii=False, indent=2)

                # 2. Produire audio_clean.mp3
                out_audio = build_audio_clean(AUDIO_IN_PATH, OUT_DIR, decision)
                dur_out   = ffprobe_duration(out_audio)

                self._json(200, {
                    "status": "validated",
                    "audio_clean": out_audio,
                    "duration_out": dur_out,
                    "decision_saved": decision_path,
                })
                print(f"[F01A] Validation reçue — audio_clean.mp3 produit ({dur_out}s)")
                # Shutdown après réponse
                threading.Timer(1.0, self.server.shutdown).start()
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self._json(404, {"error": "not found"})


def main():
    global AUDIO_IN_PATH, OUT_DIR
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True, help="Chemin vers audio_raw.mp3")
    ap.add_argument("--out",   required=True, help="Dossier OUT pour audio_clean + décision")
    ap.add_argument("--port",  type=int, default=PORT)
    args = ap.parse_args()

    AUDIO_IN_PATH = args.audio
    OUT_DIR       = args.out

    print(f"[F01A] Serveur sur port {args.port}")
    print(f"[F01A] Audio  : {AUDIO_IN_PATH}")
    print(f"[F01A] OUT    : {OUT_DIR}")

    server = http.server.HTTPServer(("0.0.0.0", args.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
