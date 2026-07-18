#!/usr/bin/env python3
"""
crs_f00_generate.py — F00 ASSETFORGE Phase 2 : Image Generation (CPU)
=====================================================================
Génère une image unique depuis le prompts_manifest.json.
Conçu pour tourner sur GitHub Actions (CPU, ubuntu-latest).

Usage:
    python crs_f00_generate.py --manifest prompts_manifest.json --index 0 --output output/

Variables d'environnement optionnelles:
    HF_TOKEN — token HuggingFace (pour télécharger FLUX.1-schnell si gated)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="F00 Phase 2 — Generate single image (CPU)")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to prompts_manifest.json")
    parser.add_argument("--index", type=int, required=True, help="Image index in manifest (0-based)")
    parser.add_argument("--output", type=Path, default=Path("output"), help="Output directory")
    args = parser.parse_args()

    # 1. Load manifest
    with open(args.manifest) as f:
        manifest = json.load(f)

    images = manifest["images"]
    if args.index >= len(images):
        print(f"ERROR: index {args.index} out of range ({len(images)} images)")
        sys.exit(1)

    img_spec = images[args.index]
    filename = img_spec["filename"]
    prompt = img_spec["prompt"]
    meta = manifest["meta"]

    print(f"\n{'='*60}")
    print(f"  F00 ASSETFORGE — Image Generation (CPU)")
    print(f"  Image {args.index + 1}/{len(images)}: {filename}")
    print(f"{'='*60}\n")

    # 2. Install dependencies
    print("[STEP 1] Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                          "diffusers", "transformers", "accelerate", "torch",
                          "pillow", "--no-warn-script-location"])
    print("  ✓ Dependencies installed")

    # 3. Import torch and diffusers
    print("\n[STEP 2] Loading PyTorch...")
    import torch
    from diffusers import FluxPipeline
    print(f"  PyTorch: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    print(f"  Device: CPU")

    # 4. Load model
    print("\n[STEP 3] Loading FLUX.1-schnell...")
    print("  (This downloads ~12GB on first run, cached afterwards)")
    t0 = time.time()

    # Use float16 to save memory, even on CPU
    # If float16 fails on CPU, fallback to float32
    try:
        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            torch_dtype=torch.float16,
            token=os.environ.get("HF_TOKEN"),
        )
    except Exception as e:
        print(f"  float16 failed: {e}")
        print("  Retrying with float32...")
        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            torch_dtype=torch.float32,
            token=os.environ.get("HF_TOKEN"),
        )

    # CPU optimizations
    pipe.enable_attention_slicing()
    try:
        pipe.enable_sequential_cpu_offload()
    except Exception:
        try:
            pipe.enable_model_cpu_offload()
        except Exception:
            pass

    load_time = time.time() - t0
    print(f"  ✓ Model loaded in {load_time:.0f}s")

    # 5. Generate image
    print(f"\n[STEP 4] Generating {filename}...")

    # Dimensions — reduced for CPU (faster, less memory)
    # Generate at 1024x576 then we could upscale, but for now keep it simple
    if meta["format"] == "VERTICAL":
        WIDTH, HEIGHT = 768, 1344  # reduced from 1080x1920
    else:
        WIDTH, HEIGHT = 1344, 768  # reduced from 1920x1080

    style_constraints = (
        "No text, no watermark, no logo in the image. "
        "High contrast, clear composition. "
        "Consistent visual style across all images."
    )
    full_prompt = f"{prompt}. {style_constraints}"

    print(f"  Prompt: {full_prompt[:100]}...")
    print(f"  Size: {WIDTH}x{HEIGHT}")
    print(f"  Steps: 4 (FLUX.1-schnell)")

    t0 = time.time()
    result = pipe(
        prompt=full_prompt,
        width=WIDTH,
        height=HEIGHT,
        num_inference_steps=4,
        guidance_scale=0.0,
    )
    image = result.images[0]
    gen_time = time.time() - t0
    print(f"  ✓ Generated in {gen_time:.0f}s")

    # 6. Save
    args.output.mkdir(parents=True, exist_ok=True)
    out_path = args.output / filename
    image.save(out_path)
    size_kb = out_path.stat().st_size / 1024
    print(f"\n[STEP 5] Saved: {out_path} ({size_kb:.0f} KB)")

    # 7. Metadata
    meta_out = {
        "filename": filename,
        "index": args.index,
        "generation_time_seconds": gen_time,
        "load_time_seconds": load_time,
        "size": f"{WIDTH}x{HEIGHT}",
        "model": "FLUX.1-schnell",
        "device": "cpu",
    }
    meta_path = args.output / f"{filename}.meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta_out, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  ✓ DONE — {filename} ({gen_time:.0f}s generation)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
