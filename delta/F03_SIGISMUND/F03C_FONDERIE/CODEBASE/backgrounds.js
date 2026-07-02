/**
 * CRUSADER Delta — F03A L'INTERPRÉTEUR
 * backgrounds.js
 *
 * Décors vivants Canvas 2D — chaque élément "respire" via Math.sin(time).
 * Système modulaire : un Background peut combiner plusieurs layers.
 *
 * Backgrounds disponibles :
 * - CityBackground      : Ville nocturne avec gratte-ciels et néons
 * - NatureBackground     : Paysage nature avec collines, arbres, nuages
 * - OfficeBackground     : Bureau/intérieur avec fenêtres et mobilier
 * - AbstractBackground   : Fond abstrait géométrique (pour transitions)
 *
 * Usage:
 *   const bg = new NatureBackground(ctx, 1920, 1080);
 *   bg.draw(time);
 */

// ─── BASE CLASS ────────────────────────────────────

class CrusaderBackground {
  constructor(ctx, width, height, options = {}) {
    this.ctx = ctx;
    this.W = width;
    this.H = height;
    this.palette = options.palette || {};
  }

  draw(time) {
    // Override in subclass
  }

  _gradient(x0, y0, x1, y1, stops) {
    const g = this.ctx.createLinearGradient(x0, y0, x1, y1);
    stops.forEach(([offset, color]) => g.addColorStop(offset, color));
    return g;
  }
}

// ─── CITY BACKGROUND ──────────────────────────────

class CityBackground extends CrusaderBackground {
  constructor(ctx, width, height, options = {}) {
    super(ctx, width, height, options);
    this.buildings = this._generateBuildings();
    this.stars = this._generateStars(80);
  }

  _generateBuildings() {
    const buildings = [];
    let x = 0;
    while (x < this.W + 100) {
      const w = 40 + Math.random() * 80;
      const h = 100 + Math.random() * 350;
      buildings.push({
        x, w, h,
        windows: Math.floor(h / 30),
        windowCols: Math.floor(w / 20),
        hue: Math.floor(Math.random() * 360),
        neonChance: Math.random(),
      });
      x += w + 5 + Math.random() * 15;
    }
    return buildings;
  }

  _generateStars(count) {
    const stars = [];
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * this.W,
        y: Math.random() * this.H * 0.4,
        size: 0.5 + Math.random() * 2,
        twinkleSpeed: 1 + Math.random() * 3,
        phase: Math.random() * Math.PI * 2,
      });
    }
    return stars;
  }

  draw(time) {
    const ctx = this.ctx;
    const W = this.W;
    const H = this.H;

    // Sky gradient — breathing color shift
    const skyShift = Math.sin(time * 0.2) * 10;
    const sky = this._gradient(0, 0, 0, H, [
      [0, `rgb(${10 + skyShift}, ${10 + skyShift}, ${40 + skyShift})`],
      [0.4, `rgb(${20 + skyShift}, ${15 + skyShift}, ${55 + skyShift})`],
      [0.8, `rgb(${30 + skyShift}, ${25 + skyShift}, ${70 + skyShift})`],
      [1, `rgb(${45 + skyShift}, ${35 + skyShift}, ${85 + skyShift})`],
    ]);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    // Stars — twinkling
    this.stars.forEach(star => {
      const alpha = 0.3 + Math.sin(time * star.twinkleSpeed + star.phase) * 0.5;
      ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, alpha)})`;
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fill();
    });

    // Moon — subtle glow
    const moonX = W * 0.8;
    const moonY = H * 0.12;
    const moonGlow = 30 + Math.sin(time * 0.5) * 10;
    ctx.fillStyle = `rgba(255, 255, 200, 0.08)`;
    ctx.beginPath();
    ctx.arc(moonX, moonY, moonGlow * 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFDE7';
    ctx.beginPath();
    ctx.arc(moonX, moonY, 25, 0, Math.PI * 2);
    ctx.fill();

    // Ground
    ctx.fillStyle = '#1A1A2E';
    ctx.fillRect(0, H * 0.75, W, H * 0.25);

    // Buildings
    this.buildings.forEach(b => {
      const groundY = H * 0.75;
      const bx = b.x;
      const by = groundY - b.h;

      // Building body
      ctx.fillStyle = `hsl(${b.hue}, 5%, 12%)`;
      ctx.fillRect(bx, by, b.w, b.h);

      // Building outline
      ctx.strokeStyle = `hsl(${b.hue}, 10%, 20%)`;
      ctx.lineWidth = 1;
      ctx.strokeRect(bx, by, b.w, b.h);

      // Windows — some lit, some dark, breathing
      for (let row = 0; row < b.windows; row++) {
        for (let col = 0; col < b.windowCols; col++) {
          const wx = bx + 8 + col * 18;
          const wy = by + 10 + row * 28;
          if (wx + 10 > bx + b.w - 5) continue;

          const isLit = Math.sin(row * 3.7 + col * 2.3 + b.hue) > -0.3;
          if (isLit) {
            const flicker = 0.5 + Math.sin(time * 2 + row + col * 0.5 + b.hue) * 0.3;
            ctx.fillStyle = `rgba(255, 220, 100, ${flicker})`;
          } else {
            ctx.fillStyle = 'rgba(20, 20, 40, 0.8)';
          }
          ctx.fillRect(wx, wy, 10, 14);
        }
      }

      // Neon sign (some buildings)
      if (b.neonChance > 0.7) {
        const neonAlpha = 0.5 + Math.sin(time * 3 + b.hue) * 0.4;
        ctx.fillStyle = `hsla(${b.hue + 180}, 100%, 60%, ${neonAlpha})`;
        ctx.fillRect(bx + b.w * 0.2, by + 15, b.w * 0.6, 6);
        // Glow
        ctx.shadowColor = `hsla(${b.hue + 180}, 100%, 60%, 0.5)`;
        ctx.shadowBlur = 15;
        ctx.fillRect(bx + b.w * 0.2, by + 15, b.w * 0.6, 6);
        ctx.shadowBlur = 0;
      }
    });

    // Ground road lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 2;
    ctx.setLineDash([30, 20]);
    ctx.beginPath();
    ctx.moveTo(0, H * 0.88);
    ctx.lineTo(W, H * 0.88);
    ctx.stroke();
    ctx.setLineDash([]);

    // Atmospheric fog at ground level — breathing
    const fogAlpha = 0.08 + Math.sin(time * 0.3) * 0.04;
    const fogGrad = this._gradient(0, H * 0.7, 0, H, [
      [0, 'rgba(100, 100, 150, 0)'],
      [1, `rgba(100, 100, 150, ${fogAlpha})`],
    ]);
    ctx.fillStyle = fogGrad;
    ctx.fillRect(0, H * 0.7, W, H * 0.3);
  }
}

// ─── NATURE BACKGROUND ────────────────────────────

class NatureBackground extends CrusaderBackground {
  constructor(ctx, width, height, options = {}) {
    super(ctx, width, height, options);
    this.clouds = this._generateClouds(6);
    this.trees = this._generateTrees(12);
  }

  _generateClouds(count) {
    const clouds = [];
    for (let i = 0; i < count; i++) {
      clouds.push({
        x: Math.random() * this.W * 1.5,
        y: 50 + Math.random() * this.H * 0.2,
        scale: 0.5 + Math.random() * 1,
        speed: 8 + Math.random() * 15,
        phase: Math.random() * Math.PI * 2,
      });
    }
    return clouds;
  }

  _generateTrees(count) {
    const trees = [];
    for (let i = 0; i < count; i++) {
      trees.push({
        x: (i / count) * this.W + Math.random() * 80 - 40,
        scale: 0.6 + Math.random() * 0.8,
        swayPhase: Math.random() * Math.PI * 2,
        swaySpeed: 0.8 + Math.random() * 0.6,
        type: Math.random() > 0.5 ? 'pine' : 'round',
      });
    }
    return trees;
  }

  draw(time) {
    const ctx = this.ctx;
    const W = this.W;
    const H = this.H;

    // Sky — breathing gradient
    const dayShift = Math.sin(time * 0.15) * 20;
    const sky = this._gradient(0, 0, 0, H * 0.6, [
      [0, `rgb(${100 + dayShift}, ${170 + dayShift}, ${240 + dayShift})`],
      [0.6, `rgb(${160 + dayShift}, ${210 + dayShift}, ${250})`],
      [1, `rgb(${200 + dayShift}, ${230 + dayShift}, ${255})`],
    ]);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    // Sun — gentle pulse
    const sunPulse = 35 + Math.sin(time * 0.8) * 3;
    ctx.fillStyle = 'rgba(255, 230, 100, 0.15)';
    ctx.beginPath();
    ctx.arc(W * 0.75, H * 0.12, sunPulse * 2.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFE066';
    ctx.beginPath();
    ctx.arc(W * 0.75, H * 0.12, sunPulse, 0, Math.PI * 2);
    ctx.fill();

    // Clouds — drifting
    this.clouds.forEach(cloud => {
      const cx = ((cloud.x + time * cloud.speed) % (W + 200)) - 100;
      const cy = cloud.y + Math.sin(time * 0.5 + cloud.phase) * 5;
      const s = cloud.scale;

      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
      ctx.beginPath();
      ctx.arc(cx, cy, 25 * s, 0, Math.PI * 2);
      ctx.arc(cx + 22 * s, cy - 8 * s, 20 * s, 0, Math.PI * 2);
      ctx.arc(cx + 40 * s, cy, 22 * s, 0, Math.PI * 2);
      ctx.arc(cx + 18 * s, cy + 5 * s, 18 * s, 0, Math.PI * 2);
      ctx.fill();
    });

    // Far hills — parallax breathing
    const hillBreath = Math.sin(time * 0.3) * 3;
    ctx.fillStyle = '#7CAE7A';
    ctx.beginPath();
    ctx.moveTo(0, H * 0.55);
    for (let x = 0; x <= W; x += 40) {
      const h = Math.sin(x * 0.003 + 1) * 40 + Math.sin(x * 0.007) * 20 + hillBreath;
      ctx.lineTo(x, H * 0.52 - h);
    }
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fill();

    // Near hills
    ctx.fillStyle = '#5B9A5B';
    ctx.beginPath();
    ctx.moveTo(0, H * 0.65);
    for (let x = 0; x <= W; x += 30) {
      const h = Math.sin(x * 0.005 + 2) * 30 + Math.sin(x * 0.01) * 15 + hillBreath * 0.5;
      ctx.lineTo(x, H * 0.62 - h);
    }
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fill();

    // Ground
    ctx.fillStyle = '#4A8C4A';
    ctx.fillRect(0, H * 0.7, W, H * 0.3);

    // Grass details
    ctx.strokeStyle = '#3D7A3D';
    ctx.lineWidth = 1.5;
    for (let x = 0; x < W; x += 15) {
      const grassSway = Math.sin(time * 2 + x * 0.1) * 4;
      const grassH = 8 + Math.sin(x * 0.3) * 5;
      ctx.beginPath();
      ctx.moveTo(x, H * 0.7);
      ctx.quadraticCurveTo(x + grassSway, H * 0.7 - grassH, x + grassSway * 1.2, H * 0.7 - grassH * 1.2);
      ctx.stroke();
    }

    // Trees — swaying
    this.trees.forEach(tree => {
      const sway = Math.sin(time * tree.swaySpeed + tree.swayPhase) * 4 * tree.scale;
      const baseY = H * 0.7;
      const s = tree.scale;
      const tx = tree.x;

      // Trunk
      ctx.fillStyle = '#5D4037';
      ctx.beginPath();
      ctx.moveTo(tx - 5 * s, baseY);
      ctx.lineTo(tx - 3 * s + sway * 0.3, baseY - 50 * s);
      ctx.lineTo(tx + 3 * s + sway * 0.3, baseY - 50 * s);
      ctx.lineTo(tx + 5 * s, baseY);
      ctx.closePath();
      ctx.fill();

      // Foliage
      if (tree.type === 'pine') {
        ctx.fillStyle = '#2E7D32';
        for (let i = 0; i < 3; i++) {
          const ly = baseY - 35 * s - i * 22 * s;
          const lw = (25 - i * 6) * s;
          ctx.beginPath();
          ctx.moveTo(tx + sway * (0.5 + i * 0.2), ly - 20 * s);
          ctx.lineTo(tx - lw + sway * (0.3 + i * 0.1), ly);
          ctx.lineTo(tx + lw + sway * (0.3 + i * 0.1), ly);
          ctx.closePath();
          ctx.fill();
        }
      } else {
        ctx.fillStyle = '#388E3C';
        ctx.beginPath();
        ctx.arc(tx + sway, baseY - 65 * s, 28 * s, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#2E7D32';
        ctx.beginPath();
        ctx.arc(tx - 12 * s + sway * 0.8, baseY - 55 * s, 20 * s, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(tx + 14 * s + sway * 1.1, baseY - 58 * s, 18 * s, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Ground path
    ctx.fillStyle = '#8D6E63';
    ctx.beginPath();
    ctx.moveTo(W * 0.3, H);
    ctx.quadraticCurveTo(W * 0.45, H * 0.75, W * 0.5, H * 0.7);
    ctx.quadraticCurveTo(W * 0.55, H * 0.75, W * 0.7, H);
    ctx.closePath();
    ctx.fill();
  }
}

// ─── OFFICE BACKGROUND ────────────────────────────

class OfficeBackground extends CrusaderBackground {
  draw(time) {
    const ctx = this.ctx;
    const W = this.W;
    const H = this.H;

    // Wall
    ctx.fillStyle = '#E8E0D4';
    ctx.fillRect(0, 0, W, H * 0.7);

    // Floor
    ctx.fillStyle = '#8B7355';
    ctx.fillRect(0, H * 0.7, W, H * 0.3);

    // Floor reflection
    const floorGrad = this._gradient(0, H * 0.7, 0, H, [
      [0, 'rgba(255, 255, 255, 0.1)'],
      [1, 'rgba(0, 0, 0, 0.05)'],
    ]);
    ctx.fillStyle = floorGrad;
    ctx.fillRect(0, H * 0.7, W, H * 0.3);

    // Window — with breathing light
    const lightPulse = 0.8 + Math.sin(time * 0.4) * 0.1;
    ctx.fillStyle = `rgba(200, 220, 255, ${lightPulse})`;
    ctx.fillRect(W * 0.1, H * 0.08, W * 0.35, H * 0.45);
    // Window frame
    ctx.strokeStyle = '#5D4037';
    ctx.lineWidth = 6;
    ctx.strokeRect(W * 0.1, H * 0.08, W * 0.35, H * 0.45);
    // Window cross
    ctx.beginPath();
    ctx.moveTo(W * 0.275, H * 0.08);
    ctx.lineTo(W * 0.275, H * 0.53);
    ctx.moveTo(W * 0.1, H * 0.3);
    ctx.lineTo(W * 0.45, H * 0.3);
    ctx.stroke();

    // Light rays from window — breathing
    ctx.fillStyle = `rgba(255, 250, 220, ${0.03 + Math.sin(time * 0.5) * 0.015})`;
    ctx.beginPath();
    ctx.moveTo(W * 0.1, H * 0.53);
    ctx.lineTo(W * 0.45, H * 0.53);
    ctx.lineTo(W * 0.65, H * 0.7);
    ctx.lineTo(0, H * 0.7);
    ctx.closePath();
    ctx.fill();

    // Desk
    ctx.fillStyle = '#5D4037';
    ctx.fillRect(W * 0.55, H * 0.5, W * 0.35, H * 0.04);
    // Desk legs
    ctx.fillRect(W * 0.57, H * 0.54, 0.015 * W, H * 0.16);
    ctx.fillRect(W * 0.87, H * 0.54, 0.015 * W, H * 0.16);

    // Monitor on desk
    ctx.fillStyle = '#333';
    ctx.fillRect(W * 0.65, H * 0.3, W * 0.15, H * 0.2);
    // Screen glow — breathing
    const screenGlow = 0.7 + Math.sin(time * 1.5) * 0.2;
    ctx.fillStyle = `rgba(100, 150, 255, ${screenGlow})`;
    ctx.fillRect(W * 0.655, H * 0.31, W * 0.14, H * 0.18);
    // Monitor stand
    ctx.fillStyle = '#333';
    ctx.fillRect(W * 0.715, H * 0.5, W * 0.02, -H * 0.02);

    // Plant — breathing/swaying
    const plantSway = Math.sin(time * 1.2) * 3;
    const plantX = W * 0.92;
    const plantY = H * 0.5;
    // Pot
    ctx.fillStyle = '#A0522D';
    ctx.beginPath();
    ctx.moveTo(plantX - 15, plantY);
    ctx.lineTo(plantX - 12, plantY + 25);
    ctx.lineTo(plantX + 12, plantY + 25);
    ctx.lineTo(plantX + 15, plantY);
    ctx.closePath();
    ctx.fill();
    // Leaves
    ctx.fillStyle = '#4CAF50';
    for (let i = 0; i < 5; i++) {
      const angle = (i / 5) * Math.PI - Math.PI / 2 + plantSway * 0.02;
      const leafLen = 20 + Math.sin(i * 2) * 8;
      ctx.beginPath();
      ctx.ellipse(
        plantX + Math.cos(angle) * leafLen * 0.5 + plantSway * (i % 2 ? 1 : -1) * 0.3,
        plantY - 5 + Math.sin(angle) * leafLen * 0.5,
        leafLen * 0.6, 6, angle, 0, Math.PI * 2
      );
      ctx.fill();
    }

    // Wall art
    ctx.strokeStyle = '#8D6E63';
    ctx.lineWidth = 3;
    ctx.strokeRect(W * 0.6, H * 0.08, W * 0.12, H * 0.15);
    ctx.fillStyle = '#E0D0C0';
    ctx.fillRect(W * 0.605, H * 0.085, W * 0.11, H * 0.14);

    // Baseboard
    ctx.fillStyle = '#5D4037';
    ctx.fillRect(0, H * 0.68, W, H * 0.02);
  }
}

// ─── ABSTRACT BACKGROUND ──────────────────────────

class AbstractBackground extends CrusaderBackground {
  constructor(ctx, width, height, options = {}) {
    super(ctx, width, height, options);
    this.shapes = this._generateShapes(20);
  }

  _generateShapes(count) {
    const shapes = [];
    for (let i = 0; i < count; i++) {
      shapes.push({
        x: Math.random() * this.W,
        y: Math.random() * this.H,
        size: 20 + Math.random() * 60,
        rotation: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.5,
        hue: Math.floor(Math.random() * 360),
        type: ['circle', 'square', 'triangle'][Math.floor(Math.random() * 3)],
        phase: Math.random() * Math.PI * 2,
        floatSpeed: 0.3 + Math.random() * 0.7,
      });
    }
    return shapes;
  }

  draw(time) {
    const ctx = this.ctx;
    const W = this.W;
    const H = this.H;

    // Deep background — breathing gradient
    const hueShift = time * 10;
    const bg = this._gradient(0, 0, W, H, [
      [0, `hsl(${(220 + hueShift) % 360}, 30%, 8%)`],
      [0.5, `hsl(${(250 + hueShift) % 360}, 25%, 12%)`],
      [1, `hsl(${(280 + hueShift) % 360}, 30%, 8%)`],
    ]);
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // Floating shapes
    this.shapes.forEach(shape => {
      const fx = shape.x + Math.sin(time * shape.floatSpeed + shape.phase) * 30;
      const fy = shape.y + Math.cos(time * shape.floatSpeed * 0.7 + shape.phase) * 20;
      const rot = shape.rotation + time * shape.rotSpeed;
      const alpha = 0.1 + Math.sin(time * 0.5 + shape.phase) * 0.08;
      const pulse = shape.size + Math.sin(time + shape.phase) * 5;

      ctx.save();
      ctx.translate(fx, fy);
      ctx.rotate(rot);
      ctx.fillStyle = `hsla(${shape.hue}, 60%, 50%, ${alpha})`;
      ctx.strokeStyle = `hsla(${shape.hue}, 70%, 60%, ${alpha * 2})`;
      ctx.lineWidth = 1.5;

      switch (shape.type) {
        case 'circle':
          ctx.beginPath();
          ctx.arc(0, 0, pulse / 2, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
          break;
        case 'square':
          ctx.fillRect(-pulse / 2, -pulse / 2, pulse, pulse);
          ctx.strokeRect(-pulse / 2, -pulse / 2, pulse, pulse);
          break;
        case 'triangle':
          ctx.beginPath();
          ctx.moveTo(0, -pulse / 2);
          ctx.lineTo(-pulse / 2, pulse / 2);
          ctx.lineTo(pulse / 2, pulse / 2);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
          break;
      }
      ctx.restore();
    });

    // Grid overlay — subtle breathing
    ctx.strokeStyle = `rgba(255, 255, 255, ${0.03 + Math.sin(time * 0.4) * 0.01})`;
    ctx.lineWidth = 0.5;
    const gridSize = 80;
    for (let x = 0; x < W; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = 0; y < H; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }
  }
}

// Export
if (typeof module !== 'undefined') {
  module.exports = { CrusaderBackground, CityBackground, NatureBackground, OfficeBackground, AbstractBackground };
}
