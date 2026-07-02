#!/usr/bin/env python3
"""
CRUSADER Delta — F03B LE SCRIPTORIUM
crs_f03b_scriptorium.py

Prend un storyboard.json + les fichiers JS (characters, backgrounds, effects)
et assemble un index.html autonome prêt pour Puppeteer.

Le HTML généré contient :
  - Tout le JS inliné (zéro dépendance externe)
  - drawFrame(frameIndex) piloté par le storyboard
  - Transitions crossfade entre scènes
  - HUD overlay avec infos de debug
  - window.CRUSADER_CONFIG pour Puppeteer

Produit aussi timing.json avec le mapping frame → temps.

Usage:
  python crs_f03b_scriptorium.py \
    --storyboard storyboard.json \
    --characters ../F03A_INTERPRETEUR/CODEBASE/characters.js \
    --backgrounds ../F03A_INTERPRETEUR/CODEBASE/backgrounds.js \
    --effects ../F03A_INTERPRETEUR/CODEBASE/effects.js \
    --output ../F03C_FONDERIE/CODEBASE/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta


def log(msg):
    tz = timezone(timedelta(hours=1))
    ts = datetime.now(tz).strftime("%H:%M:%S")
    print(f"[F03B {ts}] {msg}")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_timing_json(storyboard, output_dir):
    """Generate frame-by-frame timing data."""
    fps = storyboard["global"]["fps"]
    scenes = storyboard["scenes"]
    timing = {
        "fps": fps,
        "total_duration": sum(s["duration"] for s in scenes),
        "total_frames": 0,
        "scenes": [],
        "frames": [],
    }

    frame_index = 0
    for scene in scenes:
        scene_frames = int(scene["duration"] * fps)
        scene_entry = {
            "id": scene["id"],
            "name": scene["name"],
            "start_frame": frame_index,
            "end_frame": frame_index + scene_frames - 1,
            "duration": scene["duration"],
            "frame_count": scene_frames,
        }
        timing["scenes"].append(scene_entry)

        for f in range(scene_frames):
            timing["frames"].append({
                "frame": frame_index,
                "time": round(frame_index / fps, 4),
                "scene_id": scene["id"],
                "scene_progress": round(f / scene_frames, 4),
            })
            frame_index += 1

    timing["total_frames"] = frame_index

    path = os.path.join(output_dir, "timing.json")
    with open(path, "w") as f:
        json.dump(timing, f, indent=2)
    log(f"✅ timing.json — {frame_index} frames, {timing['total_duration']}s")
    return timing


def generate_index_html(storyboard, js_files, timing, output_dir):
    """Assemble the self-contained index.html."""

    fps = storyboard["global"]["fps"]
    width = storyboard["global"]["width"]
    height = storyboard["global"]["height"]
    total_frames = timing["total_frames"]
    total_duration = timing["total_duration"]
    char_scale = storyboard["global"].get("character_scale", 2.5)
    transition_dur = storyboard["global"].get("transition_duration", 0.4)
    palette = storyboard.get("character", {}).get("palette", {})

    # Build scenes JS array from storyboard
    scenes_js_array = "[\n"
    for s in storyboard["scenes"]:
        c = s["character"]
        e = s.get("effects", {})
        particles = f'"{e["particles"]}"' if e.get("particles") else "null"
        text_escaped = s.get("text", "").replace("'", "\\'").replace('"', '\\"')
        scenes_js_array += f"""    {{
      id: "{s['id']}",
      name: "{s['name']}",
      duration: {s['duration']},
      background: "{s['background']}",
      posture: "{c['posture']}",
      emotion: "{c['emotion']}",
      direction: {c['direction']},
      charStartX: {c['start_x']},
      charEndX: {c['end_x']},
      charYRatio: {c['y_ratio']},
      particles: {particles},
      vignette: {str(e.get('vignette', True)).lower()},
      text: "{text_escaped}",
    }},
"""
    scenes_js_array += "  ]"

    # Palette JS
    palette_js = json.dumps(palette) if palette else "{}"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>CRUSADER Delta — F03B Scriptorium Output</title>
  <style>
    * {{ margin: 0; padding: 0; }}
    body {{ background: #000; overflow: hidden; }}
    canvas {{ display: block; }}
  </style>
</head>
<body>
  <canvas id="canvas" width="{width}" height="{height}"></canvas>

  <script>
// ═══════════════════════════════════════════════════
// INLINED: characters.js
// ═══════════════════════════════════════════════════
{js_files['characters']}

// ═══════════════════════════════════════════════════
// INLINED: backgrounds.js
// ═══════════════════════════════════════════════════
{js_files['backgrounds']}

// ═══════════════════════════════════════════════════
// INLINED: effects.js
// ═══════════════════════════════════════════════════
{js_files['effects']}

// ═══════════════════════════════════════════════════
// SCRIPTORIUM — Scene Engine (generated)
// ═══════════════════════════════════════════════════
(function() {{
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const W = {width};
  const H = {height};
  const FPS = {fps};
  const TOTAL_FRAMES = {total_frames};
  const TOTAL_DURATION = {total_duration};
  const TRANSITION_DURATION = {transition_dur};

  // ─── Scenes from storyboard.json ───
  const scenes = {scenes_js_array};

  // ─── Pre-compute scene timing ───
  let cumulTime = 0;
  scenes.forEach(s => {{
    s._startTime = cumulTime;
    s._endTime = cumulTime + s.duration;
    s._startFrame = Math.round(cumulTime * FPS);
    s._endFrame = Math.round((cumulTime + s.duration) * FPS) - 1;
    cumulTime += s.duration;
  }});

  // ─── Instantiate objects ───
  const backgrounds = {{
    nature: new NatureBackground(ctx, W, H),
    city: new CityBackground(ctx, W, H),
    office: new OfficeBackground(ctx, W, H),
    abstract: new AbstractBackground(ctx, W, H),
  }};

  const character = new CrusaderCharacter(ctx, {{
    scale: {char_scale},
    palette: {palette_js},
  }});

  const particleSystems = {{
    dust: new ParticleSystem(ctx, W, H, {{ type: 'dust', count: 40 }}),
    sparks: new ParticleSystem(ctx, W, H, {{ type: 'sparks', count: 30 }}),
    rain: new ParticleSystem(ctx, W, H, {{ type: 'rain', count: 60 }}),
    snow: new ParticleSystem(ctx, W, H, {{ type: 'snow', count: 50 }}),
  }};

  const vignette = new VignetteEffect(ctx, W, H, {{ intensity: 0.35 }});
  const textOverlay = new TextOverlay(ctx, {{
    font: 'bold 28px monospace',
    color: '#FFFFFF',
  }});
  const titleOverlay = new TextOverlay(ctx, {{
    font: 'bold 36px monospace',
    color: '#FFFFFF',
  }});
  const subtitleOverlay = new TextOverlay(ctx, {{
    font: '24px sans-serif',
    color: 'rgba(255,255,255,0.8)',
  }});

  // ─── Find scene for a given frame ───
  function getSceneAtFrame(frameIndex) {{
    const time = frameIndex / FPS;
    for (let i = 0; i < scenes.length; i++) {{
      if (time < scenes[i]._endTime) return i;
    }}
    return scenes.length - 1;
  }}

  // ─── Main draw function ───
  function drawFrame(frameIndex) {{
    const globalTime = frameIndex / FPS;
    const sceneIdx = getSceneAtFrame(frameIndex);
    const scene = scenes[sceneIdx];
    const sceneTime = globalTime - scene._startTime;
    const sceneProgress = Math.min(1, sceneTime / scene.duration);

    // Clear
    ctx.clearRect(0, 0, W, H);

    // Background
    if (backgrounds[scene.background]) {{
      backgrounds[scene.background].draw(globalTime);
    }}

    // Scene transition (crossfade in)
    if (sceneTime < TRANSITION_DURATION) {{
      const fadeAlpha = 1 - (sceneTime / TRANSITION_DURATION);
      ctx.fillStyle = 'rgba(0, 0, 0, ' + fadeAlpha + ')';
      ctx.fillRect(0, 0, W, H);
    }}

    // Scene transition (crossfade out)
    const timeToEnd = scene.duration - sceneTime;
    if (timeToEnd < TRANSITION_DURATION && sceneIdx < scenes.length - 1) {{
      const fadeAlpha = 1 - (timeToEnd / TRANSITION_DURATION);
      ctx.fillStyle = 'rgba(0, 0, 0, ' + fadeAlpha + ')';
      ctx.fillRect(0, 0, W, H);
    }}

    // Particles behind character
    if (scene.particles && scene.particles !== 'sparks' && particleSystems[scene.particles]) {{
      particleSystems[scene.particles].draw(globalTime);
    }}

    // Character
    const charX = scene.charStartX + (scene.charEndX - scene.charStartX) * sceneProgress;
    const charY = H * scene.charYRatio;
    character.setState(scene.posture, scene.emotion, scene.direction);
    character.draw(charX, charY, globalTime);

    // Particles in front (sparks)
    if (scene.particles === 'sparks' && particleSystems.sparks) {{
      particleSystems.sparks.draw(globalTime);
    }}

    // Vignette
    if (scene.vignette) {{
      vignette.draw(globalTime);
    }}

    // Scene text (subtitle)
    if (scene.text) {{
      subtitleOverlay.draw(scene.text, W / 2, H - 80, sceneTime, {{
        typing: true,
        typingSpeed: 12,
      }});
    }}

    // Final scene fade to black
    if (sceneIdx === scenes.length - 1 && sceneProgress > 0.7) {{
      const finalFade = (sceneProgress - 0.7) / 0.3;
      ctx.fillStyle = 'rgba(0, 0, 0, ' + finalFade + ')';
      ctx.fillRect(0, 0, W, H);
    }}

    // HUD
    ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
    ctx.fillRect(0, 0, W, 80);

    titleOverlay.draw('CRUSADER Delta — F03B SCRIPTORIUM', W / 2, 28, globalTime);
    textOverlay.draw(
      'Scene ' + (sceneIdx + 1) + '/' + scenes.length + ': ' + scene.name +
      '  |  Frame: ' + frameIndex + '/' + TOTAL_FRAMES +
      '  |  ' + scene.posture + ' / ' + scene.emotion,
      W / 2, 58, globalTime
    );

    // Progress bar
    const progress = frameIndex / TOTAL_FRAMES;
    ctx.fillStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.fillRect(30, H - 35, W - 60, 10);
    ctx.fillStyle = '#3498DB';
    ctx.fillRect(30, H - 35, (W - 60) * progress, 10);

    // Scene markers
    let markerTime = 0;
    for (let i = 0; i < scenes.length - 1; i++) {{
      markerTime += scenes[i].duration;
      const markerX = 30 + (W - 60) * (markerTime / TOTAL_DURATION);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.fillRect(markerX, H - 38, 1, 16);
    }}
  }}

  // Expose for Puppeteer
  window.CRUSADER_CONFIG = {{ FPS: FPS, DURATION: TOTAL_DURATION, TOTAL_FRAMES: TOTAL_FRAMES, W: W, H: H }};
  window.drawFrame = drawFrame;

  // Auto-play preview in browser
  let currentFrame = 0;
  function animate() {{
    drawFrame(currentFrame);
    currentFrame = (currentFrame + 1) % TOTAL_FRAMES;
    requestAnimationFrame(animate);
  }}
  animate();
}})();
  </script>
</body>
</html>"""

    path = os.path.join(output_dir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"✅ index.html — {len(html):,} bytes, {len(storyboard['scenes'])} scenes, {total_frames} frames")
    return path


def main():
    parser = argparse.ArgumentParser(description="F03B Le Scriptorium — CRUSADER Delta")
    parser.add_argument("--storyboard", required=True, help="Path to storyboard.json")
    parser.add_argument("--characters", required=True, help="Path to characters.js")
    parser.add_argument("--backgrounds", required=True, help="Path to backgrounds.js")
    parser.add_argument("--effects", required=True, help="Path to effects.js")
    parser.add_argument("--output", default=".", help="Output directory")
    args = parser.parse_args()

    log("═══════════════════════════════════════════")
    log("   F03B LE SCRIPTORIUM — CRUSADER Delta   ")
    log("   Assemblage du moteur de rendu          ")
    log("═══════════════════════════════════════════")

    # Read inputs
    log("Reading storyboard...")
    storyboard = json.loads(read_file(args.storyboard))
    log(f"  {len(storyboard['scenes'])} scenes, "
        f"{sum(s['duration'] for s in storyboard['scenes'])}s total")

    log("Reading JS modules...")
    js_files = {
        "characters": read_file(args.characters),
        "backgrounds": read_file(args.backgrounds),
        "effects": read_file(args.effects),
    }
    for name, content in js_files.items():
        log(f"  {name}.js — {len(content):,} bytes")

    # Generate outputs
    os.makedirs(args.output, exist_ok=True)

    log("Generating timing.json...")
    timing = generate_timing_json(storyboard, args.output)

    log("Assembling index.html...")
    html_path = generate_index_html(storyboard, js_files, timing, args.output)

    log("═══════════════════════════════════════════")
    log(f"  ✅ SCRIPTORIUM COMPLETE")
    log(f"  Output: {args.output}")
    log(f"  index.html: ready for Puppeteer")
    log(f"  timing.json: {timing['total_frames']} frames @ {timing['fps']}fps")
    log("═══════════════════════════════════════════")


if __name__ == "__main__":
    main()
