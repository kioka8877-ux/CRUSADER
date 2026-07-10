#!/usr/bin/env python3
"""
CRS F00 — EXTRACT
Extrait en batch depuis une vidéo :
  - Frames clés (1 frame/sec ou détection changement de scène)
  - GIFs animés (séquences courtes 2-5s en boucle)
  - Clips MP4 courts (5-10s pour usage ultérieur)
Utilise FFmpeg.
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import timedelta


def get_video_duration(video_path: str) -> float:
    """Retourne la durée de la vidéo en secondes via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def extract_frames(video_path: str, output_dir: str, fps: int = 1) -> list[str]:
    """
    Extrait 1 frame par seconde (ou fps personnalisé).
    Output : frame_000001.png, frame_000002.png, ...
    """
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%06d.png")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        "-y", pattern
    ]

    print(f"[EXTRACT] Frames @ {fps}fps → {output_dir}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[EXTRACT] ERREUR frames: {result.stderr[-500:]}")
        return []

    frames = sorted(Path(output_dir).glob("frame_*.png"))
    print(f"[EXTRACT] {len(frames)} frames extraites")
    return [str(f) for f in frames]


def extract_gifs(video_path: str, output_dir: str, duration: int = 3, interval: int = 10) -> list[str]:
    """
    Extrait des GIFs animés de {duration} secondes, toutes les {interval} secondes.
    """
    os.makedirs(output_dir, exist_ok=True)
    gifs = []

    try:
        total_duration = get_video_duration(video_path)
    except Exception:
        total_duration = 0

    if total_duration == 0:
        print("[EXTRACT] Impossible de déterminer la durée, skip GIFs")
        return []

    # Calculer combien de GIFs on peut faire
    start = 0
    gif_num = 1
    while start + duration <= total_duration:
        gif_path = os.path.join(output_dir, f"gif_{gif_num:04d}.gif")

        # Palette + GIF en 2 passes pour la qualité
        palette_cmd = [
            "ffmpeg", "-ss", str(start), "-t", str(duration),
            "-i", video_path,
            "-vf", "fps=15,scale=480:-1:flags=lanczos,palettegen",
            "-y", "/tmp/palette.png"
        ]
        gif_cmd = [
            "ffmpeg", "-ss", str(start), "-t", str(duration),
            "-i", video_path, "-i", "/tmp/palette.png",
            "-lavfi", "fps=15,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse",
            "-y", gif_path
        ]

        subprocess.run(palette_cmd, capture_output=True, text=True)
        result = subprocess.run(gif_cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(gif_path):
            gifs.append(gif_path)
            print(f"[EXTRACT] GIF {gif_num}: {start}s→{start+duration}s")
        else:
            print(f"[EXTRACT] GIF {gif_num} échoué (start={start}s)")

        start += interval
        gif_num += 1

    print(f"[EXTRACT] {len(gifs)} GIFs extraits")
    return gifs


def extract_clips(video_path: str, output_dir: str, duration: int = 8, interval: int = 30) -> list[str]:
    """
    Extrait des clips MP4 courts de {duration} secondes, toutes les {interval} secondes.
    """
    os.makedirs(output_dir, exist_ok=True)
    clips = []

    try:
        total_duration = get_video_duration(video_path)
    except Exception:
        total_duration = 0

    if total_duration == 0:
        print("[EXTRACT] Impossible de déterminer la durée, skip clips")
        return []

    start = 0
    clip_num = 1
    while start + duration <= total_duration:
        clip_path = os.path.join(output_dir, f"clip_{clip_num:04d}.mp4")

        cmd = [
            "ffmpeg", "-ss", str(start), "-t", str(duration),
            "-i", video_path,
            "-c", "copy",
            "-y", clip_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(clip_path):
            clips.append(clip_path)
            print(f"[EXTRACT] Clip {clip_num}: {start}s→{start+duration}s")
        else:
            # Fallback : re-encode si copy échoue
            cmd_reencode = [
                "ffmpeg", "-ss", str(start), "-t", str(duration),
                "-i", video_path,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                "-y", clip_path
            ]
            result2 = subprocess.run(cmd_reencode, capture_output=True, text=True)
            if result2.returncode == 0 and os.path.exists(clip_path):
                clips.append(clip_path)
                print(f"[EXTRACT] Clip {clip_num} (re-encode): {start}s→{start+duration}s")

        start += interval
        clip_num += 1

    print(f"[EXTRACT] {len(clips)} clips extraits")
    return clips


def extract_all(video_path: str, output_base: str, fps: int = 1,
                gif_duration: int = 3, clip_duration: int = 8) -> dict:
    """
    Extrait frames + GIFs + clips depuis une vidéo.
    Retourne un dict avec les chemins.
    """
    video_name = Path(video_path).stem
    base = os.path.join(output_base, video_name)

    frames = extract_frames(video_path, os.path.join(base, "frames"), fps)
    gifs = extract_gifs(video_path, os.path.join(base, "gifs"), gif_duration)
    clips = extract_clips(video_path, os.path.join(base, "clips"), clip_duration)

    return {
        "video": video_path,
        "video_name": video_name,
        "frames": frames,
        "gifs": gifs,
        "clips": clips,
        "frame_count": len(frames),
        "gif_count": len(gifs),
        "clip_count": len(clips)
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="F00 EXTRACT — FFmpeg batch extraction")
    parser.add_argument("video", help="Chemin de la vidéo")
    parser.add_argument("--output", default="./extracted", help="Dossier de sortie")
    parser.add_argument("--fps", type=int, default=1, help="Frames par seconde")
    parser.add_argument("--gif-duration", type=int, default=3, help="Durée GIFs (s)")
    parser.add_argument("--clip-duration", type=int, default=8, help="Durée clips (s)")
    args = parser.parse_args()

    result = extract_all(args.video, args.output, args.fps,
                         args.gif_duration, args.clip_duration)
    print(f"\n[EXTRACT] Terminé: {result['frame_count']} frames, "
          f"{result['gif_count']} GIFs, {result['clip_count']} clips")
    print(json.dumps(result, indent=2))
