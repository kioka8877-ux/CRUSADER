/* F02 CRUSADER Preview — Pure JS Engine */

let roadmap, timing;
let playing = false;
let animId = null;
let currentFrame = 0;

const BG_OPTIONS = [
  { label: "Couleur unie", value: "solid" },
  { label: "Quadrillé bleu", value: "bg_grid_dark.png" },
  { label: "Bleu uni", value: "bg_solid_blue.png" },
  { label: "Papier neuf", value: "bg_paper_new.png" },
  { label: "Papier froissé", value: "bg_paper_crumpled.png" },
  { label: "Papyrus ancien", value: "bg_papyrus_old.png" },
];

const FONTS = ["Cinzel","Playfair Display","Lato","Oswald","Roboto Slab","Inter","Arial Black","Helvetica"];

// ── Default style overrides ──
const defaults = {
  world_scale: 0.70,
  world_next_scale: 0.35,
  world_opacity: 1.0,
  world_next_opacity: 0.3,
  camera_amplitude: 200,
  camera_spacing: 1500,
  background_type: "solid",
  background_image: "",
  background_color: "#F5F0E8",
  background_scale: 1.0,
  subtitle_font: "Cinzel",
  subtitle_size: 44,
  subtitle_color: "#FFFFFF",
  subtitle_position: "bottom",
  subtitle_align: "center",
  grain_intensity: 0.15,
  vignette: true,
};

let style = {};

function getS(key) {
  return style[key] ?? roadmap?.style?.[key] ?? defaults[key];
}
function setS(key, val) {
  style[key] = val;
  renderAll();
}

// ── Init ──
(async function init() {
  roadmap = await (await fetch("roadmap.json")).json();
  timing = await (await fetch("timing.json")).json();
  const totalFrames = timing.meta.total_frames;

  document.getElementById("timeline").max = totalFrames - 1;
  document.getElementById("frameLabel").textContent = `Frame 0 / ${totalFrames}`;

  buildControls();
  renderAll();

  // Timeline scrubber
  const tl = document.getElementById("timeline");
  tl.addEventListener("input", () => {
    currentFrame = parseInt(tl.value);
    document.getElementById("frameLabel").textContent = `Frame ${currentFrame} / ${totalFrames}`;
    renderAll();
  });

  // Play/Pause
  document.getElementById("btnPlay").addEventListener("click", () => {
    playing = !playing;
    document.getElementById("btnPlay").textContent = playing ? "⏸ Pause" : "▶ Play";
    if (playing) animate();
    else cancelAnimationFrame(animId);
  });

  function animate() {
    if (!playing) return;
    currentFrame = (currentFrame + 1) % totalFrames;
    tl.value = currentFrame;
    document.getElementById("frameLabel").textContent = `Frame ${currentFrame} / ${totalFrames}`;
    renderAll();
    animId = requestAnimationFrame(animate);
  }

  // Export — ouvre une nouvelle fenêtre pour contourner l'iframe sandboxée
  document.getElementById("btnExport").addEventListener("click", () => {
    const merged = { ...roadmap, style: { ...roadmap.style, ...style } };
    const json = JSON.stringify(merged, null, 2);
    const w = window.open("", "_blank");
    if (w) {
      w.document.write(`<!DOCTYPE html><html><head><title>roadmap.json</title></head><body>
        <pre style="white-space:pre-wrap;word-break:break-all;font-size:12px;font-family:monospace;max-width:900px;margin:20px auto;">${json.replace(/</g,"&lt;").replace(/>/g,"&gt;")}</pre>
        <script>
          var a=document.createElement("a");
          a.href="data:application/json;charset=utf-8,"+encodeURIComponent(${JSON.stringify(json)});
          a.download="roadmap.json";
          document.body.appendChild(a);
          a.click();
        <\/script></body></html>`);
      w.document.close();
    } else {
      // Fallback: copier dans le presse-papier
      navigator.clipboard.writeText(json).then(() => {
        alert("roadmap.json copié dans le presse-papier ! Colle-le dans un fichier.");
      }).catch(() => {
        // Dernier recours: textarea
        const ta = document.createElement("textarea");
        ta.value = json;
        ta.style.cssText = "position:fixed;top:10%;left:10%;width:80%;height:80%;z-index:99999;font-size:11px;font-family:monospace;";
        document.body.appendChild(ta);
        ta.select();
        alert("Copie le contenu (Ctrl+A puis Ctrl+C) et colle dans roadmap.json");
      });
    }
  });
})();

// ── Build controls panel ──
function buildControls() {
  const c = document.getElementById("controls");
  c.innerHTML = `
    ${section("📐 Capsules")}
    ${slider("world_scale", "Taille visuel actif", 0.2, 1, 0.05)}
    ${slider("world_next_scale", "Taille visuel N+1", 0.1, 1, 0.05)}
    ${slider("world_opacity", "Opacité actif", 0, 1, 0.05)}
    ${slider("world_next_opacity", "Opacité N+1", 0, 1, 0.01)}

    ${section("🎥 Caméra sinusoïdale")}
    ${slider("camera_amplitude", "Amplitude (px)", 0, 500, 10)}
    ${slider("camera_spacing", "Espacement (px)", 500, 3000, 50)}

    ${section("🖼️ Background")}
    ${select("background_image", "Type", BG_OPTIONS.map(o => o.value), BG_OPTIONS.map(o => o.label))}
    ${color("background_color", "Couleur fond")}
    ${slider("background_scale", "Scale fond", 0.5, 2, 0.05)}

    ${section("📝 Sous-titres")}
    ${select("subtitle_font", "Police", FONTS, FONTS)}
    ${slider("subtitle_size", "Taille", 16, 80, 2)}
    ${color("subtitle_color", "Couleur")}
    ${select("subtitle_position", "Position", ["top","center","bottom"], ["Haut","Centre","Bas"])}
    ${select("subtitle_align", "Alignement", ["left","center","right"], ["Gauche","Centre","Droite"])}

    ${section("🎨 Effets")}
    ${slider("grain_intensity", "Grain", 0, 0.5, 0.01)}
  `;

  // Bind events
  c.querySelectorAll("input[type=range]").forEach(el => {
    el.addEventListener("input", () => {
      const v = parseFloat(el.value);
      setS(el.dataset.key, v);
      el.closest(".ctrl-row").querySelector(".val").textContent = v;
    });
  });
  c.querySelectorAll("select").forEach(el => {
    el.addEventListener("change", () => {
      setS(el.dataset.key, el.value);
    });
  });
  c.querySelectorAll("input[type=color]").forEach(el => {
    el.addEventListener("input", () => {
      setS(el.dataset.key, el.value);
      el.closest(".ctrl-row").querySelector(".val").textContent = el.value;
    });
  });
}

function section(t) { return `<div class="section-title">${t}</div>`; }
function slider(key, label, min, max, step) {
  const v = getS(key);
  return `<div class="ctrl-row"><label><span>${label}</span><span class="val">${v}</span></label><input type="range" data-key="${key}" min="${min}" max="${max}" step="${step}" value="${v}"></div>`;
}
function select(key, label, values, labels) {
  const v = getS(key);
  const opts = values.map((val, i) => `<option value="${val}" ${val === v ? "selected" : ""}>${labels[i]}</option>`).join("");
  return `<div class="ctrl-row"><label>${label}</label><select data-key="${key}">${opts}</select></div>`;
}
function color(key, label) {
  const v = getS(key);
  return `<div class="ctrl-row" style="display:flex;align-items:center;gap:8px"><input type="color" data-key="${key}" value="${v}"><label style="flex:1">${label}</label><span class="val" style="font-size:10px">${v}</span></div>`;
}

// ── Render engine ──
function renderAll() {
  renderViewport("viewport-desktop");
  renderViewport("viewport-iphone");
}

function renderViewport(id) {
  const container = document.getElementById(id);
  const rect = container.getBoundingClientRect();
  const vW = rect.width;
  const vH = rect.height;
  if (vW === 0 || vH === 0) return;

  const tl = roadmap.timeline;
  const totalFrames = timing.meta.total_frames;

  // ── Style values ──
  const worldScale = parseFloat(getS("world_scale"));
  const worldNextScale = parseFloat(getS("world_next_scale"));
  const worldOpacity = parseFloat(getS("world_opacity"));
  const worldNextOpacity = parseFloat(getS("world_next_opacity"));
  const camAmplitude = parseFloat(getS("camera_amplitude"));
  const camSpacing = parseFloat(getS("camera_spacing"));
  const bgImage = getS("background_image");
  const bgColor = getS("background_color");
  const bgScale = parseFloat(getS("background_scale"));
  const subFont = getS("subtitle_font");
  const subSize = parseFloat(getS("subtitle_size"));
  const subColor = getS("subtitle_color");
  const subPos = getS("subtitle_position");
  const subAlign = getS("subtitle_align");

  // ── Scale factor (viewport px / composition px) ──
  const compW = roadmap.meta.width || 1920;
  const compH = roadmap.meta.height || 1080;
  const sf = Math.min(vW / compW, vH / compH);

  // ── Find active segment ──
  let segIdx = 0;
  for (let i = tl.length - 1; i >= 0; i--) {
    if (currentFrame >= tl[i].start_frame) { segIdx = i; break; }
  }
  const seg = tl[segIdx];
  const nextSeg = tl[segIdx + 1] || null;
  const segEnd = nextSeg ? nextSeg.start_frame : totalFrames;
  const tf = seg.trans_frames || 12;
  const transStart = segEnd - tf;

  // ── Camera progress ──
  let camProgress = segIdx;
  if (currentFrame >= transStart && nextSeg) {
    const rawT = clamp01((currentFrame - transStart) / tf);
    const t = bezierEase(rawT);
    camProgress = segIdx + t;
  }

  const camX = camProgress * camSpacing * sf;
  const camY = camAmplitude * Math.cos(camProgress * Math.PI) * sf;
  const txX = vW / 2 - camX;
  const txY = vH / 2 - camY;

  // ── Build HTML ──
  let html = "";

  // Background
  if (bgImage && bgImage !== "solid") {
    html += `<div class="viewport-bg"><img src="${bgImage}" style="transform:scale(${bgScale});transform-origin:center center;"></div>`;
  } else {
    html += `<div class="viewport-bg" style="background:${bgColor}"></div>`;
  }

  // World container
  html += `<div class="world-container" style="transform:translate(${txX}px,${txY}px)">`;

  for (let i = 0; i < tl.length; i++) {
    const s = tl[i];
    const posX = i * camSpacing * sf;
    const posY = camAmplitude * Math.cos(i * Math.PI) * sf;

    const dist = Math.abs(i - camProgress);
    const t = Math.min(dist, 1);
    const thisScale = worldScale + (worldNextScale - worldScale) * t;
    const thisOpacity = (worldOpacity + (worldNextOpacity - worldOpacity) * t) * clamp01(1.5 - dist);

    if (thisOpacity <= 0.01) continue;

    const wW = compW * thisScale * sf;
    const wH = compH * thisScale * sf;
    const left = posX - wW / 2;
    const top = posY - wH / 2;

    html += `<div class="world-node" style="left:${left}px;top:${top}px;width:${wW}px;height:${wH}px;opacity:${thisOpacity.toFixed(3)}">`;
    html += `<img src="${s.image_file}" loading="lazy">`;
    html += `</div>`;
  }
  html += `</div>`;

  // Subtitle
  const subText = seg.text_subtitles;
  if (subText) {
    const fontSize = subSize * sf;
    let posCSS = "";
    if (subPos === "top") posCSS = "top:8%";
    else if (subPos === "center") posCSS = "top:50%;transform:translateY(-50%)";
    else posCSS = "bottom:8%";

    html += `<div class="subtitle-overlay" style="${posCSS};text-align:${subAlign}">`;
    html += `<div style="font-family:'${subFont}',Georgia,serif;font-size:${Math.max(fontSize, 8)}px;color:${subColor};text-shadow:0 2px 8px rgba(0,0,0,0.85);line-height:1.3">${subText}</div>`;
    html += `</div>`;
  }

  container.innerHTML = html;
}

// ── Utils ──
function clamp01(v) { return Math.max(0, Math.min(1, v)); }
function bezierEase(t) {
  // Approximation of cubic-bezier(0.42, 0, 0.58, 1)
  return t * t * (3 - 2 * t); // smoothstep — close enough
}
