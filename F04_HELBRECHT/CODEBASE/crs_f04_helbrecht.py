"""
crs_f04_helbrecht.py — Frégate F04 HELBRECHT
=============================================
Remux FFmpeg de short_render.mp4, injection métadonnées issues de timing.json,
optimisation streaming (faststart), production de final_master.mp4.

Usage:
    python crs_f04_helbrecht.py \\
        --input   /path/to/F04/IN/ \\
        --output  /path/to/F04/OUT/

Dépendances système :
    ffmpeg >= 4.0 (installé dans le notebook via apt-get)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import date

# ─── Constantes ───────────────────────────────────────────────────────────────

INPUT_VIDEO   = "short_render.mp4"
INPUT_TIMING  = "timing.json"
OUTPUT_VIDEO  = "final_master.mp4"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log_ok(msg):
    print(f"  [OK]   {msg}")

def log_fail(msg):
    print(f"  [FAIL] {msg}")

def log_info(msg):
    print(f"  [...]  {msg}")

def check_ffmpeg():
    """Vérifie que ffmpeg est disponible."""
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode != 0:
        log_fail("ffmpeg non trouvé. Installez-le : apt-get install -y ffmpeg")
        sys.exit(1)
    version_line = result.stdout.splitlines()[0] if result.stdout else "version inconnue"
    log_ok(f"ffmpeg disponible — {version_line}")

def read_timing_meta(timing_path: str) -> dict:
    """Lit timing.json et extrait les métadonnées utiles."""
    if not os.path.isfile(timing_path):
        log_fail(f"timing.json introuvable : {timing_path}")
        sys.exit(1)

    with open(timing_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    log_ok(f"timing.json lu — meta : {meta}")
    return meta

def build_metadata_args(meta: dict) -> list:
    """Construit les arguments -metadata pour ffmpeg depuis la meta timing."""
    today = date.today().isoformat()

    title   = meta.get("title",   "CRUSADER_SHORT")
    comment = meta.get("comment", "Pipeline CRUSADER — Frégate HELBRECHT")
    fps     = meta.get("fps",     30)
    fmt     = meta.get("format",  "vertical")

    description = (
        f"Produit par le pipeline CRUSADER. "
        f"Format : {fmt}. "
        f"FPS : {fps}. "
        f"Date : {today}."
    )

    args = [
        "-metadata", f"title={title}",
        "-metadata", f"comment={comment}",
        "-metadata", f"description={description}",
        "-metadata", f"date={today}",
        "-metadata", "encoder=CRUSADER v1.0 — F04 HELBRECHT",
    ]
    return args

def remux(input_video: str, output_video: str, metadata_args: list):
    """Lance le remux FFmpeg : copie flux, inject métadonnées, faststart."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
    ] + metadata_args + [output_video]

    print(f"[CMD] {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        log_fail(f"ffmpeg a échoué (exit {result.returncode})")
        sys.exit(result.returncode)

def verify_output(output_path: str) -> float:
    """Vérifie que la sortie existe et retourne sa taille en MB."""
    if not os.path.isfile(output_path):
        log_fail(f"Fichier absent après remux : {output_path}")
        sys.exit(1)

    size_bytes = os.path.getsize(output_path)
    if size_bytes < 100_000:
        log_fail(f"Fichier trop petit ({size_bytes} bytes) — rendu probablement corrompu.")
        sys.exit(1)

    size_mb = size_bytes / (1024 * 1024)
    log_ok(f"{output_path} — {size_mb:.1f} MB")
    return size_mb

def probe_video(video_path: str):
    """Affiche les informations de la vidéo finale (durée, codec, résolution)."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        log_info("ffprobe indisponible — informations vidéo ignorées.")
        return

    try:
        info = json.loads(result.stdout)
        fmt = info.get("format", {})
        duration = float(fmt.get("duration", 0))
        minutes, seconds = divmod(int(duration), 60)
        log_ok(f"Durée : {minutes}m{seconds:02d}s")

        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                w = stream.get("width",  "?")
                h = stream.get("height", "?")
                codec = stream.get("codec_name", "?")
                log_ok(f"Vidéo : {codec} {w}×{h}")
            elif stream.get("codec_type") == "audio":
                codec = stream.get("codec_name", "?")
                sr = stream.get("sample_rate", "?")
                log_ok(f"Audio : {codec} {sr} Hz")
    except (json.JSONDecodeError, ValueError):
        log_info("Impossible de parser les infos ffprobe.")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F04 HELBRECHT — Remux FFmpeg + Métadonnées")
    parser.add_argument("--input",  required=True, help="Chemin vers F04/IN/")
    parser.add_argument("--output", required=True, help="Chemin vers F04/OUT/")
    args = parser.parse_args()

    input_video  = os.path.join(args.input,  INPUT_VIDEO)
    input_timing = os.path.join(args.input,  INPUT_TIMING)
    output_video = os.path.join(args.output, OUTPUT_VIDEO)

    os.makedirs(args.output, exist_ok=True)

    print()
    print("═══════════════════════════════════════════")
    print("  F04 HELBRECHT — Remux & Finalisation")
    print("═══════════════════════════════════════════")
    print(f"  IN    : {args.input}")
    print(f"  OUT   : {args.output}")
    print()

    # ── 1. Vérification ffmpeg ───────────────────────────────────────────────
    log_info("Vérification ffmpeg...")
    check_ffmpeg()

    # ── 2. Vérification fichiers d'entrée ────────────────────────────────────
    log_info(f"Vérification {INPUT_VIDEO}...")
    if not os.path.isfile(input_video):
        log_fail(f"short_render.mp4 introuvable : {input_video}")
        sys.exit(1)
    size_in = os.path.getsize(input_video) / (1024 * 1024)
    log_ok(f"{input_video} ({size_in:.1f} MB)")

    # ── 3. Lecture métadonnées ───────────────────────────────────────────────
    log_info("Lecture timing.json...")
    meta = read_timing_meta(input_timing)
    metadata_args = build_metadata_args(meta)

    # ── 4. Remux FFmpeg ──────────────────────────────────────────────────────
    print()
    log_info("Remux FFmpeg en cours...")
    remux(input_video, output_video, metadata_args)

    # ── 5. Vérification sortie ───────────────────────────────────────────────
    log_info("Vérification final_master.mp4...")
    size_mb = verify_output(output_video)

    # ── 6. Probe vidéo ───────────────────────────────────────────────────────
    log_info("Analyse de la vidéo finale...")
    probe_video(output_video)

    print()
    print("═══════════════════════════════════════════")
    print("  HELBRECHT — MISSION ACCOMPLIE")
    print(f"  {output_video}")
    print(f"  Taille : {size_mb:.1f} MB")
    print("═══════════════════════════════════════════")
    print()


if __name__ == "__main__":
    main()
