#!/usr/bin/env python3
"""
crs_f00_phase1.py — F00 ASSETFORGE Phase 1 : Prompt Generation
================================================================
Transforme les segments Whisper (timing.json) + le style extrait (style_prompt.txt)
en prompts image exploitables par FLUX.1-schnell.

Produit prompts_manifest.json avec:
  - meta: mode, format, total_images, style_prompt_hash
  - images[]: filename, start_seconds, segments_covered, text_source, prompt, overlay, intensite

Usage:
    python crs_f00_phase1.py --mode GROUPED --format HORIZONTAL
    python crs_f00_phase1.py --mode 1:1 --format VERTICAL

Variables d'environnement requises:
    AI_GATEWAY_BASE_URL — URL de base de l'AI Gateway
    AI_GATEWAY_API_KEY  — clé API de l'AI Gateway

Stdlib uniquement. requests auto-installé si absent.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
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

SCRIPT_DIR   = Path(__file__).parent.resolve()
F00_ROOT     = SCRIPT_DIR.parent
F01_OUT      = F00_ROOT.parent / "F01_GRIMALDUS" / "F01B_GRIMALDUS" / "OUT"
TIMING_PATH  = F01_OUT / "timing.json"
STYLE_PATH   = F00_ROOT / "OUT" / "style_prompt.txt"
MANIFEST_OUT = F00_ROOT / "OUT" / "prompts_manifest.json"

GROUPING_MODEL   = os.environ.get("F00_GROUPING_MODEL", "anthropic/claude-haiku-4.5")
PROMPT_GEN_MODEL = os.environ.get("F00_PROMPT_MODEL", "anthropic/claude-haiku-4.5")

SYSTEM_PROMPT_GROUPING = """\
You are a video segment grouping assistant.
You will receive a JSON array of narration segments with text, start, and end times.
Group segments that cover the same idea or narrative scene.

Rules:
- Create groups of 3 to 6 segments each
- Aim for 5 to 8 groups total
- Each segment must belong to exactly one group
- Groups must be contiguous (segments in a group must be consecutive)
- Preserve original segment indices

Output format (JSON only, no markdown):
[
  {"segments": [0, 1, 2], "theme": "brief theme description"},
  {"segments": [3, 4, 5], "theme": "brief theme description"}
]
"""

SYSTEM_PROMPT_IMAGE = """\
You are an image prompt engineer for AI image generation models.
You will receive:
1. A visual style description (style_prompt.txt)
2. A segment group with its text

Your task: write a single image generation prompt in English.

Rules:
- 50-80 words max
- Pure visual description — no narration, no text in image
- Integrate the style description naturally
- No text, watermarks, logos in the described image
- High contrast, clear composition
- Also output: overlay type and intensity (see values below)

Overlay values: INTERIEUR:neons | INTERIEUR:lampe | INTERIEUR:ecran | INTERIEUR:sombre |
EXTERIEUR:pluie | EXTERIEUR:vent | EXTERIEUR:soleil | EXTERIEUR:nuit |
VITRE:pluie | VITRE:brouillard | defaut

Intensity: 1 (subtle) / 2 (normal) / 3 (dramatic — only for high emotional impact scenes)

Output format (JSON only, no markdown):
{"prompt": "...", "overlay": "...", "intensite": 2}
"""

# ── Helpers ─────────────────────────────────────────────────────────────────

def timestamp_to_filename(seconds):
    """Convertit un timestamp en secondes vers MM_SS_mmm.png."""
    total_ms = int(round(seconds * 1000))
    minutes = total_ms // 60000
    secs    = (total_ms % 60000) // 1000
    millis  = total_ms % 1000
    return f"{minutes:02d}_{secs:02d}_{millis:03d}.png"


def call_llm(base_url, api_key, model, system_prompt, user_content, max_tokens=1000):
    """Appel générique à l'AI Gateway (format OpenAI-compatible)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }
    resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
    if not resp.ok:
        raise RuntimeError(f"[LLM] API error {resp.status_code}: {resp.text[:500]}")
    return resp.json()["choices"][0]["message"]["content"].strip()


def extract_json_from_response(text):
    """Extrait le JSON d'une réponse LLM (gère markdown code blocks)."""
    # Retirer les code blocks markdown si présents
    if "```" in text:
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block or not line.strip().startswith("```"):
                json_lines.append(line)
        text = "\n".join(json_lines)
    return json.loads(text.strip())


def group_segments(segments, base_url, api_key):
    """Groupe les segments via LLM (mode GROUPED)."""
    # Préparer le résumé des segments pour le LLM
    seg_summary = json.dumps([
        {"id": s["id"], "text": s["text"], "start": s["start"], "end": s["end"]}
        for s in segments
    ], ensure_ascii=False, indent=2)

    print(f"[GROUPING] Envoi de {len(segments)} segments au modèle {GROUPING_MODEL}...")
    raw = call_llm(base_url, api_key, GROUPING_MODEL, SYSTEM_PROMPT_GROUPING, seg_summary)
    groups = extract_json_from_response(raw)
    print(f"[GROUPING] {len(groups)} groupes créés")
    return groups


def generate_image_prompt(segment_texts, style_prompt, base_url, api_key):
    """Génère un prompt image pour un groupe de segments."""
    user_content = f"""STYLE DESCRIPTION:
{style_prompt}

SEGMENT TEXT TO ILLUSTRATE:
{chr(10).join(f'- {t}' for t in segment_texts)}

Generate the image prompt following the system prompt rules. JSON output only."""

    raw = call_llm(base_url, api_key, PROMPT_GEN_MODEL, SYSTEM_PROMPT_IMAGE, user_content)
    result = extract_json_from_response(raw)
    return result


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F00 Phase 1 — Prompt Generation")
    parser.add_argument("--mode",   choices=["GROUPED", "1:1"], default="GROUPED",
                        help="Mode de génération (défaut: GROUPED)")
    parser.add_argument("--format", choices=["VERTICAL", "HORIZONTAL"], default="HORIZONTAL",
                        help="Format d'image (défaut: HORIZONTAL)")
    parser.add_argument("--timing",  type=Path, default=TIMING_PATH,
                        help="Chemin vers timing.json")
    parser.add_argument("--style",   type=Path, default=STYLE_PATH,
                        help="Chemin vers style_prompt.txt")
    parser.add_argument("--output",  type=Path, default=MANIFEST_OUT,
                        help="Chemin de sortie prompts_manifest.json")
    args = parser.parse_args()

    # Vérifs
    if not args.timing.exists():
        print(f"[ERREUR] timing.json introuvable: {args.timing}")
        sys.exit(1)
    if not args.style.exists():
        print(f"[ERREUR] style_prompt.txt introuvable: {args.style}")
        sys.exit(1)

    base_url = os.environ.get("AI_GATEWAY_BASE_URL", "")
    api_key  = os.environ.get("AI_GATEWAY_API_KEY", "")
    if not base_url or not api_key:
        print("[ERREUR] AI_GATEWAY_BASE_URL et AI_GATEWAY_API_KEY doivent être définis.")
        sys.exit(1)

    # Phase 1
    print("\n═══════════════════════════════════════════════════════════")
    print("  F00 ASSETFORGE — Phase 1 : Prompt Generation")
    print(f"  Mode: {args.mode} | Format: {args.format}")
    print("═══════════════════════════════════════════════════════════\n")

    # 1. Charger les inputs
    with open(args.timing, encoding="utf-8") as f:
        timing = json.load(f)
    segments = timing.get("segments", [])
    style_prompt = args.style.read_text(encoding="utf-8").strip()
    style_hash = hashlib.md5(style_prompt.encode()).hexdigest()[:8]
    print(f"[INPUT] {len(segments)} segments | style hash: {style_hash}")

    # 2. Grouper les segments
    if args.mode == "GROUPED":
        groups = group_segments(segments, base_url, api_key)
    else:
        # Mode 1:1 — chaque segment est son propre groupe
        groups = [{"segments": [s["id"]], "theme": s["text"][:60]} for s in segments]

    # 3. Générer les prompts image pour chaque groupe
    print(f"\n[PROMPT GEN] Génération de {len(groups)} prompts image...")
    images_manifest = []

    for i, group in enumerate(groups):
        seg_indices = group["segments"]
        group_segments = [segments[idx] for idx in seg_indices if idx < len(segments)]
        if not group_segments:
            print(f"  [WARN] Groupe {i+1} vide, ignoré")
            continue

        segment_texts = [s["text"] for s in group_segments]
        first_start = group_segments[0]["start"]
        filename = timestamp_to_filename(first_start)

        print(f"  [{i+1}/{len(groups)}] {filename} — seg {seg_indices} — \"{group.get('theme', '')[:40]}\"")

        result = generate_image_prompt(segment_texts, style_prompt, base_url, api_key)

        images_manifest.append({
            "filename": filename,
            "start_seconds": first_start,
            "segments_covered": seg_indices,
            "text_source": " ".join(segment_texts),
            "prompt": result.get("prompt", ""),
            "overlay": result.get("overlay", "defaut"),
            "intensite": result.get("intensite", 2),
        })

    # 4. Écrire le manifest
    manifest = {
        "meta": {
            "mode": args.mode,
            "format": args.format,
            "total_images": len(images_manifest),
            "style_prompt_hash": style_hash,
        },
        "images": images_manifest,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] prompts_manifest.json écrit → {args.output}")
    print(f"     {len(images_manifest)} images à générer")
    print("\n═══════════════════════════════════════════════════════════")
    print("  Phase 1 TERMINÉE ✓")
    print("═══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
