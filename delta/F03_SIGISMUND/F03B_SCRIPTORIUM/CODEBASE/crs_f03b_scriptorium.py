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
    """Assemble the self-contained index.html with gamma-style framing."""

    fps = storyboard["global"]["fps"]
    width = storyboard["global"]["width"]
    height = storyboard["global"]["height"]
    total_frames = timing["total_frames"]
    total_duration = timing["total_duration"]
    char_scale = storyboard["global"].get("character_scale", 2.5)
    transition_dur = storyboard["global"].get("transition_duration", 0.5)
    palette = storyboard.get("character", {}).get("palette", {})
    prod_title = storyboard["global"].get("production_title", storyboard.get("title", "CRUSADER"))
    grain_intensity = storyboard["global"].get("grain_intensity", 0.12)
    bg_color = storyboard["global"].get("background_color", "#0D0D1A")
    sub_font = storyboard["global"].get("subtitle_font", "Georgia, serif")
    sub_size = storyboard["global"].get("subtitle_size", 44)
    sub_color = storyboard["global"].get("subtitle_color", "#FFFFFF")
    accent_color = storyboard["global"].get("accent_color", "#FFD700")
    title_font = storyboard["global"].get("title_font", "Georgia, serif")
    title_size = storyboard["global"].get("title_size", 32)
    world_title_visible = storyboard["global"].get("world_title_visible", True)

    # Build scenes JS array from storyboard
    scenes_js_array = "[\n"
    for s in storyboard["scenes"]:
        c = s["character"]
        e = s.get("effects", {})
        particles = f'"{e["particles"]}"' if e.get("particles") else "null"
        text_escaped = s.get("text", "").replace("'", "\\'").replace('"', '\\"')
        world_title = s.get("world_title", s["name"]).replace("'", "\\'").replace('"', '\\"')
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
      worldTitle: "{world_title}",
    }},
"""
    scenes_js_array += "  ]"

    # Palette JS
    palette_js = json.dumps(palette) if palette else "{}"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{prod_title} — CRUSADER Delta</title>
  <style>
    * {{ margin: 0; padding: 0; }}
    body {{ background: {bg_color}; overflow: hidden; }}
    canvas {{ display: block; }}
  </style>
</head>
<body>
  <canvas id="canvas" width="{width}" height="{height}"></canvas>

  <!-- Film grain SVG (like gamma Background.jsx) -->
  <svg id="grain-svg" width="0" height="0" style="position:absolute">
    <filter id="grain-filter">
      <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="4" seed="0" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
  </svg>

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
// Gamma-style framing: title, grain, vignette, subtitles
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
  const PROD_TITLE = "{prod_title}";
  const GRAIN_INTENSITY = {grain_intensity};
  const BG_COLOR = "{bg_color}";

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

  const vignette = new VignetteEffect(ctx, W, H, {{ intensity: 0.4 }});

  // ─── Grain canvas (offscreen, drawn as overlay) ───
  const grainCanvas = document.createElement('canvas');
  grainCanvas.width = W;
  grainCanvas.height = H;
  const grainCtx = grainCanvas.getContext('2d');

  function drawGrain(frameIndex) {{
    // Change grain pattern every 3 frames (like gamma)
    const seed = Math.floor(frameIndex / 3) % 64;
    // Simple procedural grain
    const imageData = grainCtx.createImageData(W / 4, H / 4);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {{
      const v = Math.random() * 255;
      data[i] = v;
      data[i+1] = v;
      data[i+2] = v;
      data[i+3] = 255;
    }}
    grainCtx.putImageData(imageData, 0, 0);
    // Draw scaled grain onto main canvas
    ctx.save();
    ctx.globalAlpha = GRAIN_INTENSITY;
    ctx.globalCompositeOperation = 'overlay';
    ctx.drawImage(grainCanvas, 0, 0, W / 4, H / 4, 0, 0, W, H);
    ctx.restore();
  }}

  // ─── Find scene for a given frame ───
  function getSceneAtFrame(frameIndex) {{
    const time = frameIndex / FPS;
    for (let i = 0; i < scenes.length; i++) {{
      if (time < scenes[i]._endTime) return i;
    }}
    return scenes.length - 1;
  }}

  // ─── World Title (alternance dessus/droite like F02 CASTELLAN) ───
  function drawWorldTitle(scene, sceneIdx, sceneTime) {{
    if (!scene.worldTitle) return;

    const title = scene.worldTitle;
    const titleSpeed = {title_speed};
    const titleGap = {title_gap};
    const isAbove = sceneIdx % 2 === 0;
    const progress = Math.min(1, sceneTime * FPS / titleSpeed);
    const eased = progress * progress * (3 - 2 * progress);

    ctx.save();
    ctx.globalAlpha = eased;
    ctx.font = 'bold {title_size}px {title_font}';
    ctx.fillStyle = '{title_color}';
    ctx.shadowColor = 'rgba(0,0,0,0.85)';
    ctx.shadowBlur = 12;
    ctx.shadowOffsetY = 2;

    if (isAbove) {{
      const dropOffset = -30 * (1 - eased);
      const tx = W / 2;
      const ty = 100 + titleGap + dropOffset;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(title, tx, ty);
      ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
      ctx.font = 'bold 14px monospace';
      ctx.fillStyle = '#666';
      ctx.globalAlpha = eased * 0.7;
      ctx.fillText('SCENE ' + (sceneIdx + 1) + '/' + scenes.length, tx, ty - {title_size} - 4);
    }} else {{
      const slideOffset = 40 * (1 - eased);
      const tx = W - 80 + slideOffset;
      const ty = H / 2;
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(title, tx, ty);
      ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
      ctx.font = 'bold 14px monospace';
      ctx.fillStyle = '#666';
      ctx.globalAlpha = eased * 0.7;
      ctx.fillText('SCENE ' + (sceneIdx + 1) + '/' + scenes.length, tx, ty + {title_size} + 8);
    }}

    ctx.restore();
  }}

  // ─── Subtitle with **mots forts** (like F02 CASTELLAN) ───
  function drawSubtitle(scene, sceneTime) {{
    if (!scene.text) return;

    const duration = scene.duration;
    const progress = Math.min(1, sceneTime / duration);
    const alpha = progress > 0.85 ? (1 - progress) / 0.15 : 1;

    // Parse **mots forts**
    const parts = [];
    const regex = /\*\*(.+?)\*\*/g;
    let lastIndex = 0, match;
    const rawText = scene.text;
    while ((match = regex.exec(rawText)) !== null) {{
      if (match.index > lastIndex) parts.push({{ text: rawText.slice(lastIndex, match.index), strong: false }});
      parts.push({{ text: match[1], strong: true }});
      lastIndex = match.index + match[0].length;
    }}
    if (lastIndex < rawText.length) parts.push({{ text: rawText.slice(lastIndex), strong: false }});
    if (parts.length === 0) parts.push({{ text: rawText, strong: false }});

    const displayText = parts.map(p => p.text).join('');
    if (!displayText) return;

    ctx.save();
    ctx.globalAlpha = alpha;
    const subY = H - 85;

    // Measure total width
    let totalWidth = 0;
    for (const part of parts) {{
      const fontSize = part.strong ? {accent_size} : {sub_size};
      const font = part.strong ? '{accent_font}' : '{sub_font}';
      ctx.font = (part.strong ? 'bold ' : '') + fontSize + 'px ' + font;
      totalWidth += ctx.measureText(part.text).width;
    }}

    // Draw text shadow
    ctx.shadowColor = 'rgba(0,0,0,0.85)';
    ctx.shadowBlur = 12;
    ctx.shadowOffsetY = 2;

    // Draw each part (no pill background)
    let drawX = W / 2 - totalWidth / 2;
    const maxFontSize = Math.max({sub_size}, {accent_size});
    const drawY = subY;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';

    for (const part of parts) {{
      const fontSize = part.strong ? {accent_size} : {sub_size};
      const font = part.strong ? '{accent_font}' : '{sub_font}';
      ctx.font = (part.strong ? 'bold ' : '') + fontSize + 'px ' + font;
      ctx.fillStyle = part.strong ? '{accent_color}' : '{sub_color}';
      ctx.fillText(part.text, drawX, drawY);
      drawX += ctx.measureText(part.text).width;
    }}

    ctx.shadowBlur = 0;
    ctx.restore();
  }}

  // ─── Production Title Bar (persistent top bar like gamma) ───
  function drawTitleBar(frameIndex) {{
    ctx.save();

    // Top bar background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.fillRect(0, 0, W, 55);

    // Bottom line accent
    ctx.fillStyle = '{accent_color}';
    ctx.fillRect(0, 53, W, 2);

    // Production title (left)
    ctx.font = 'bold 22px {title_font}';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '{accent_color}';
    ctx.fillText('⚔ ' + PROD_TITLE, 25, 27);

    // Engine badge (right)
    ctx.font = '14px monospace';
    ctx.textAlign = 'right';
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.fillText('VIBEFORGE · Canvas2D · ' + W + '×' + H + ' · ' + FPS + 'fps', W - 25, 20);

    // Frame counter (right)
    ctx.fillText('Frame ' + frameIndex + '/' + TOTAL_FRAMES, W - 25, 38);

    ctx.restore();
  }}

  // ─── Progress Bar (bottom) ───
  function drawProgressBar(frameIndex, sceneIdx) {{
    ctx.save();

    const barY = H - 20;
    const barH = 4;
    const barX = 0;
    const barW = W;
    const progress = frameIndex / TOTAL_FRAMES;

    // Bar background
    ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.fillRect(barX, barY, barW, barH);

    // Bar fill
    ctx.fillStyle = '{accent_color}';
    ctx.fillRect(barX, barY, barW * progress, barH);

    // Scene markers
    let markerTime = 0;
    for (let i = 0; i < scenes.length - 1; i++) {{
      markerTime += scenes[i].duration;
      const markerX = barW * (markerTime / TOTAL_DURATION);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.fillRect(markerX, barY - 2, 1, barH + 4);
    }}

    ctx.restore();
  }}

  // ─── Main draw function ───
  function drawFrame(frameIndex) {{
    const globalTime = frameIndex / FPS;
    const sceneIdx = getSceneAtFrame(frameIndex);
    const scene = scenes[sceneIdx];
    const sceneTime = globalTime - scene._startTime;
    const sceneProgress = Math.min(1, sceneTime / scene.duration);

    // Clear with background color
    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, W, H);

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

    // Vignette (like gamma — radial gradient)
    if (scene.vignette) {{
      vignette.draw(globalTime);
    }}

    // Film grain overlay (like gamma Background.jsx)
    drawGrain(frameIndex);

    // World Title (like gamma WorldTitle.jsx)
    drawWorldTitle(scene, sceneIdx, sceneTime);

    // Subtitle (like gamma BetaSubtitle.jsx)
    drawSubtitle(scene, sceneTime);

    // Title bar (persistent top)
    drawTitleBar(frameIndex);

    // Progress bar (bottom)
    drawProgressBar(frameIndex, sceneIdx);

    // Final scene fade to black
    if (sceneIdx === scenes.length - 1 && sceneProgress > 0.7) {{
      const finalFade = (sceneProgress - 0.7) / 0.3;
      ctx.fillStyle = 'rgba(0, 0, 0, ' + finalFade + ')';
      ctx.fillRect(0, 0, W, H);
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
