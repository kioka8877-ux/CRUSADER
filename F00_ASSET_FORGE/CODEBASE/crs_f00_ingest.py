#!/usr/bin/env python3
"""
CRS F00 — INGEST
Télécharge des vidéos sources depuis URLs (NASA, NOAA, ESA, USGS, Internet Archive, YouTube).
Utilise yt-dlp pour le téléchargement.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from urllib.parse import urlparse


def download_video(url: str, output_dir: str = "./downloads") -> str:
    """
    Télécharge une vidéo via yt-dlp.
    Retourne le chemin du fichier téléchargé.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Format : best video mp4, fallback best
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "--no-playlist",
        "--no-warnings",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        url
    ]

    print(f"[INGEST] Téléchargement: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[INGEST] ERREUR yt-dlp: {result.stderr}")
        # Fallback : download direct si URL directe (.mp4)
        if url.endswith((".mp4", ".webm", ".mov")):
            print(f"[INGEST] Fallback download direct: {url}")
            filename = os.path.basename(urlparse(url).path)
            filepath = os.path.join(output_dir, filename)
            subprocess.run(["curl", "-sL", "-o", filepath, url], check=True)
            return filepath
        raise RuntimeError(f"Échec téléchargement: {url}\n{result.stderr}")

    # Trouver le fichier téléchargé
    files = list(Path(output_dir).glob("*"))
    if not files:
        raise RuntimeError(f"Aucun fichier trouvé après téléchargement: {url}")

    # Le plus récent
    latest = max(files, key=lambda f: f.stat().st_mtime)
    print(f"[INGEST] Téléchargé: {latest} ({latest.stat().st_size / 1e6:.1f} MB)")
    return str(latest)


def ingest_urls(urls: list[str], output_dir: str = "./downloads") -> list[dict]:
    """
    Télécharge plusieurs vidéos. Retourne une liste de métadonnées.
    """
    results = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            filepath = download_video(url, output_dir)
            results.append({
                "source_url": url,
                "local_path": filepath,
                "filename": os.path.basename(filepath),
                "size_bytes": os.path.getsize(filepath),
                "status": "ok"
            })
        except Exception as e:
            results.append({
                "source_url": url,
                "status": "error",
                "error": str(e)
            })
            print(f"[INGEST] ÉCHEC: {url} — {e}")

    return results


if __name__ == "__main__":
    # Usage: python crs_f00_ingest.py "url1,url2" --output ./downloads
    import argparse
    parser = argparse.ArgumentParser(description="F00 INGEST — Download source videos")
    parser.add_argument("urls", help="URLs séparées par virgules")
    parser.add_argument("--output", default="./downloads", help="Dossier de sortie")
    args = parser.parse_args()

    url_list = args.urls.split(",")
    results = ingest_urls(url_list, args.output)

    print(f"\n[INGEST] Terminé: {len([r for r in results if r['status'] == 'ok'])} réussis, "
          f"{len([r for r in results if r['status'] == 'error'])} échoués")
    print(json.dumps(results, indent=2))
