#!/usr/bin/env python3
"""
CRS F00 — INGEST
Télécharge des vidéos sources depuis URLs (NASA, NOAA, ESA, USGS, Internet Archive, YouTube).
Utilise yt-dlp pour le télchargement, avec fallback curl (SSL bypass si nécessaire).
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from urllib.parse import urlparse


def download_video(url: str, output_dir: str = "./downloads") -> str:
    """
    Télécharge une vidéo via yt-dlp, puis curl avec SSL bypass si nécessaire.
    Retourne le chemin du fichier téléchargé.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Étape 1: yt-dlp
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "--no-playlist",
        "--no-warnings",
        "--no-check-certificates",  # Bypass SSL verification
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        url
    ]

    print(f"[INGEST] Téléchargement: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        files = list(Path(output_dir).glob("*"))
        if files:
            latest = max(files, key=lambda f: f.stat().st_mtime)
            if latest.stat().st_size > 0:
                print(f"[INGEST] Téléchargé: {latest} ({latest.stat().st_size / 1e6:.1f} MB)")
                return str(latest)

    print(f"[INGEST] yt-dlp échec, fallback curl...")

    # Étape 2: curl avec SSL bypass pour URLs directes
    if url.endswith((".mp4", ".webm", ".mov", ".mkv")):
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(output_dir, filename)

        # curl avec --insecure pour bypass SSL
        curl_cmd = [
            "curl", "-sL", "--insecure",
            "-o", filepath,
            url
        ]
        result2 = subprocess.run(curl_cmd, capture_output=True, text=True)

        if result2.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            size_mb = os.path.getsize(filepath) / 1e6
            print(f"[INGEST] Téléchargé (curl): {filepath} ({size_mb:.1f} MB)")
            return filepath

        # Étape 3: wget fallback
        print(f"[INGEST] curl échec, fallback wget...")
        wget_cmd = [
            "wget", "--no-check-certificate",
            "-q", "-O", filepath,
            url
        ]
        result3 = subprocess.run(wget_cmd, capture_output=True, text=True)

        if result3.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            size_mb = os.path.getsize(filepath) / 1e6
            print(f"[INGEST] Téléchargé (wget): {filepath} ({size_mb:.1f} MB)")
            return filepath

    raise RuntimeError(f"Échec téléchargement: {url} (yt-dlp + curl + wget ont tous échoué)")


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
