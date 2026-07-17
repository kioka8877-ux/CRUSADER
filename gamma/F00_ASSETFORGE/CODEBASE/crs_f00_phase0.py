#!/usr/bin/env python3
"""
crs_f00_phase0.py — F00 ASSETFORGE Phase 0 : Style Extraction
================================================================
Extrait le style visuel depuis :
  - Une capture d'écran (image unique) → mode SCREENSHOT
  - Ou une vidéo de référence → mode VIDEO (12 frames via FFmpeg)

Envoie les images à un modèle vision via l'AI Gateway,
produit style_prompt.txt (150-300 mots).

Usage:
    # Mode screenshot (recommandé pour test rapide)
    python crs_f00_phase0.py --input IN/reference_screenshot.png

    # Mode vidéo (extraction 12 frames)
    python crs_f00_phase0.py --input IN/reference_video.mp4

    # Output personnalisé
    python crs_f00_phase0.py --input IN/shot.png --output OUT/style_prompt.txt

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
SCREENSHOT_MAX_WIDTH = 1280
VISION_MODEL     = os.environ.get("F00_VISION_MODEL", "anthropic/claude-sonnet-4.6")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}

SYSTEM_PROMPT_VISION = """\
You are a visual art director analyzing reference video frames.
You will receive multiple frames from the same video (or a single screenshot).
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

def detect_input_type(input_path):
    """Détecte si l'input est une image ou une vidéo."""
    ext = input_path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "screenshot"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    else:
        # Fallback : essayer ffprobe
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", str(input_path)],
            capture_output=True
        )
        if result.returncode == 0:
            return "video"
        return "screenshot"


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


def resize_screenshot(image_path, output_dir):
    """Redimensionne une capture d'écran si trop large (garde l'original sinon)."""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(image_path),
            "-vf", f"scale='min({SCREENSHOT_MAX_WIDTH},iw)':-1",
            str(output_dir / "screenshot_resized.jpg")
        ], capture_output=True, check=True)
        return [output_dir / "screenshot_resized.jpg"]
    except subprocess.CalledProcessError:
        # FFmpeg échec → utiliser l'image telle quelle
        return [image_path]


def encode_frame_base64(frame_path):
    """Encode une image en base64 data URI."""
    with open(frame_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    # Détecter le mime type
    ext = Path(frame_path).suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext[1:]}"
    return f"data:{mime};base64,{data}"


def call_vision_api(frames, base_url, api_key, input_type="screenshot"):
    """Envoie les frames au modèle vision et retourne la description de style."""
    content = []
    for frame_path in frames:
        b64 = encode_frame_base64(frame_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": b64}
        })

    if input_type == "screenshot":
        instruction = (
            "Analyze this screenshot from a reference video and extract the visual style. "
            "Follow the system prompt format exactly."
        )
    else:
        instruction = (
            "Analyze these frames from the same video and extract the visual style. "
            "Follow the system prompt format exactly."
        )

    content.append({
        "type": "text",
        "text": instruction
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

    print(f"[VISION] Envoi de {len(frames)} image(s) au modèle {VISION_MODEL}...")
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
                        help="Vidéo de référence OU capture d'écran (png/jpg/mp4...)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help="Fichier de sortie (défaut: OUT/style_prompt.txt)")
    args = parser.parse_args()

    # Vérifs
    if not args.input.exists():
        print(f"[ERREUR] Fichier introuvable: {args.input}")
        print(f"  Formats acceptés: image ({', '.join(IMAGE_EXTENSIONS)}) "
              f"ou vidéo ({', '.join(VIDEO_EXTENSIONS)})")
        sys.exit(1)

    base_url = os.environ.get("AI_GATEWAY_BASE_URL", "")
    api_key  = os.environ.get("AI_GATEWAY_API_KEY", "")
    if not base_url or not api_key:
        print("[ERREUR] AI_GATEWAY_BASE_URL et AI_GATEWAY_API_KEY doivent être définis.")
        sys.exit(1)

    # Détecter le type d'input
    input_type = detect_input_type(args.input)

    # Phase 0
    print("\n═══════════════════════════════════════════════════════════")
    print("  F00 ASSETFORGE — Phase 0 : Style Extraction")
    print(f"  Mode: {input_type.upper()} | Input: {args.input.name}")
    print("═══════════════════════════════════════════════════════════\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        if input_type == "video":
            print("[STEP 1] Extraction des frames via FFmpeg...")
            frames = extract_frames(args.input, tmpdir)
        else:
            print("[STEP 1] Préparation de la capture d'écran...")
            frames = resize_screenshot(args.input, tmpdir)
            print(f"  [SCREENSHOT] {frames[0].name} prêt")

        # 2. Envoyer au modèle vision
        print(f"\n[STEP 2] Analyse visuelle via {VISION_MODEL}...")
        style_text = call_vision_api(frames, base_url, api_key, input_type)

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
