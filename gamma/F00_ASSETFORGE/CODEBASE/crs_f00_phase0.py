#!/usr/bin/env python3
"""
crs_f00_phase0.py — F00 ASSETFORGE Phase 0 : Style Extraction
================================================================
Extrait 12 frames d'une vidéo de référence via FFmpeg,
les envoie à un modèle vision via l'AI Gateway,
produit style_prompt.txt (150-300 mots).

Usage:
    python crs_f00_phase0.py [--input IN/reference_video.mp4] [--output OUT/style_prompt.txt]

Variables d'environnement requises:
    AI_GATEWAY_BASE_URL — URL de base de l'AI Gateway (ex: https://gateway.example.com/v1)
    AI_GATEWAY_API_KEY  — clé API de l'AI Gateway

Stdlib uniquement. requests auto-installé si absent (convention CRS_EXECUTEUR).
"""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Dépendance requests (auto-install si absente) ───────────────────────────
try:
    import requests
except ImportError:
    print("[SETUP] Installation de requests...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "requests",
        "--quiet", "--break-system-packages"
    ])
    import requests

# ── Constantes ──────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent.resolve()
F00_ROOT    = SCRIPT_DIR.parent
DEFAULT_IN  = F00_ROOT / "IN" / "reference_video.mp4"
DEFAULT_OUT = F00_ROOT / "OUT" / "style_prompt.txt"

NUM_FRAMES       = 12
FRAME_MAX_WIDTH  = 1280
SKIP_START_SECS  = 5
SKIP_END_SECS    = 5
VISION_MODEL     = os.environ.get("F00_VISION_MODEL", "anthropic/claude-sonnet-4.6")

SYSTEM_PROMPT_VISION = """\
You are a visual art director analyzing reference video frames.
You will receive multiple frames from the same video.
Extract and describe the visual style precisely.

Output a structured description covering:
- Visual type: (stickman / photo-realistic / illustration / whiteboard / other)
- Line style: thickness, regularity, color
- Color palette: background color, main elements color, accent colors (use hex if identifiable)
- Texture: paper grain / flat / chalkboard / digital clean / other
- Character proportions: relative to frame size
- Composition: density of elements, margins, framing
- Overall mood: minimalist / busy / playful / serious / cinematic

Be precise and factual. No interpretation. 150-200 words max.
This description will be injected directly into image generation prompts.
"""

# ── Helpers ─────────────────────────────────────────────────────────────────

def get_video_duration(video_path):
    """Retourne la durée de la vidéo en secondes via ffprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", str(video_path)
    ], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe échec: {result.stderr}")
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def extract_frames(video_path, output_dir, num_frames=NUM_FRAMES):
    """Extrait N frames réparties uniformément, en évitant début/fin."""
    duration = get_video_duration(video_path)
    usable_start = SKIP_START_SECS
    usable_end   = duration - SKIP_END_SECS
    if usable_end <= usable_start:
        # Vidéo trop courte — on prend tout
        usable_start = 0
        usable_end   = duration

    interval = (usable_end - usable_start) / (num_frames - 1) if num_frames > 1 else 0
    timestamps = [usable_start + i * interval for i in range(num_frames)]

    frames = []
    for i, ts in enumerate(timestamps):
        out_file = output_dir / f"frame_{i:02d}.jpg"
        subprocess.run([
            "ffmpeg", "-y", "-ss", f"{ts:.3f}", "-i", str(video_path),
            "-frames:v", "1", "-vf", f"scale='min({FRAME_MAX_WIDTH},iw)':-1",
            "-q:v", "2", str(out_file)
        ], capture_output=True, check=True)
        frames.append(out_file)
        print(f"  [FRAME] {i+1}/{num_frames} @ {ts:.1f}s → {out_file.name}")

    return frames


def encode_frame_base64(frame_path):
    """Encode une image en base64 data URI."""
    with open(frame_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{data}"


def call_vision_api(frames, base_url, api_key):
    """Envoie les frames au modèle vision et retourne la description de style."""
    # Construire le message utilisateur avec les images
    content = []
    for frame_path in frames:
        b64 = encode_frame_base64(frame_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": b64}
        })
    content.append({
        "type": "text",
        "text": "Analyze these frames from the same video and extract the visual style. "
                "Follow the system prompt format exactly."
    })

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_VISION},
            {"role": "user", "content": content},
        ],
        "max_tokens": 600,
        "temperature": 0.3,
    }

    print(f"[VISION] Envoi de {len(frames)} frames au modèle {VISION_MODEL}...")
    resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
    if not resp.ok:
        raise RuntimeError(f"[VISION] API error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    style_text = data["choices"][0]["message"]["content"].strip()
    return style_text


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F00 Phase 0 — Style Extraction")
    parser.add_argument("--input",  type=Path, default=DEFAULT_IN,
                        help="Vidéo de référence (défaut: IN/reference_video.mp4)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help="Fichier de sortie (défaut: OUT/style_prompt.txt)")
    args = parser.parse_args()

    # Vérifs
    if not args.input.exists():
        print(f"[ERREUR] Vidéo de référence introuvable: {args.input}")
        sys.exit(1)

    base_url = os.environ.get("AI_GATEWAY_BASE_URL", "")
    api_key  = os.environ.get("AI_GATEWAY_API_KEY", "")
    if not base_url or not api_key:
        print("[ERREUR] AI_GATEWAY_BASE_URL et AI_GATEWAY_API_KEY doivent être définis.")
        sys.exit(1)

    # Phase 0
    print("\n═══════════════════════════════════════════════════════════")
    print("  F00 ASSETFORGE — Phase 0 : Style Extraction")
    print("═══════════════════════════════════════════════════════════\n")

    # 1. Extraire les frames
    print("[STEP 1] Extraction des frames via FFmpeg...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        frames = extract_frames(args.input, tmpdir)

        # 2. Envoyer au modèle vision
        print(f"\n[STEP 2] Analyse visuelle via {VISION_MODEL}...")
        style_text = call_vision_api(frames, base_url, api_key)

    # 3. Sauvegarder
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(style_text, encoding="utf-8")
    word_count = len(style_text.split())
    print(f"\n[OK] style_prompt.txt écrit → {args.output} ({word_count} mots)")
    print("\n--- Aperçu ---")
    print(style_text[:500])
    if len(style_text) > 500:
        print("...")
    print("\n═══════════════════════════════════════════════════════════")
    print("  Phase 0 TERMINÉE ✓")
    print("═══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
