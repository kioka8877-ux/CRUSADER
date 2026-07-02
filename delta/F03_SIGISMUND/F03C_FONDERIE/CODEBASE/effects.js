/**
 * CRUSADER Delta — F03A L'INTERPRÉTEUR
 * effects.js
 *
 * Effets visuels Canvas 2D pour enrichir les scènes.
 * - ParticleSystem   : Particules génériques (poussière, pluie, neige, étincelles)
 * - ScreenShake      : Tremblement d'écran pour les moments dramatiques
 * - VignetteEffect   : Assombrissement des bords
 * - TextOverlay      : Texte animé avec typing effect
 */

// ─── PARTICLE SYSTEM ──────────────────────────────

class ParticleSystem {
  constructor(ctx, width, height, options = {}) {
    this.ctx = ctx;
    this.W = width;
    this.H = height;
    this.type = options.type || 'dust'; // dust, rain, snow, sparks
    this.count = options.count || 50;
    this.particles = [];
    this._init();
  }

  _init() {
    for (let i = 0; i < this.count; i++) {
      this.particles.push(this._createParticle());
    }
  }

  _createParticle() {
    const configs = {
      dust: {
        x: Math.random() * this.W,
        y: Math.random() * this.H,
        vx: (Math.random() - 0.5) * 0.3,
        vy: -0.2 - Math.random() * 0.3,
        size: 1 + Math.random() * 2.5,
        alpha: 0.1 + Math.random() * 0.3,
        color: '255, 255, 255',
        life: Math.random(),
      },
      rain: {
        x: Math.random() * this.W,
        y: Math.random() * this.H,
        vx: -1,
        vy: 8 + Math.random() * 6,
        size: 1,
        length: 10 + Math.random() * 15,
        alpha: 0.2 + Math.random() * 0.3,
        color: '150, 180, 255',
        life: Math.random(),
      },
      snow: {
        x: Math.random() * this.W,
        y: Math.random() * this.H,
        vx: (Math.random() - 0.5) * 0.5,
        vy: 0.5 + Math.random() * 1.5,
        size: 2 + Math.random() * 4,
        alpha: 0.3 + Math.random() * 0.5,
        color: '255, 255, 255',
        wobble: Math.random() * Math.PI * 2,
        wobbleSpeed: 1 + Math.random() * 2,
        life: Math.random(),
      },
      sparks: {
        x: this.W * 0.5 + (Math.random() - 0.5) * 100,
        y: this.H * 0.5,
        vx: (Math.random() - 0.5) * 4,
        vy: -2 - Math.random() * 4,
        size: 1 + Math.random() * 2,
        alpha: 0.5 + Math.random() * 0.5,
        color: '255, 200, 50',
        life: Math.random(),
        decay: 0.005 + Math.random() * 0.01,
      },
    };
    return { ...configs[this.type] };
  }

  draw(time) {
    const ctx = this.ctx;

    this.particles.forEach((p, i) => {
      // Update position
      p.x += p.vx;
      p.y += p.vy;

      // Type-specific behavior
      if (this.type === 'snow') {
        p.x += Math.sin(time * p.wobbleSpeed + p.wobble) * 0.5;
      }

      if (this.type === 'sparks') {
        p.vy += 0.05; // gravity
        p.alpha -= p.decay;
      }

      if (this.type === 'dust') {
        p.alpha = (0.1 + Math.random() * 0.2) * (0.5 + Math.sin(time + i) * 0.5);
      }

      // Recycle particles
      if (p.y > this.H + 20 || p.y < -20 || p.x > this.W + 20 || p.x < -20 || p.alpha <= 0) {
        const newP = this._createParticle();
        if (this.type === 'rain' || this.type === 'snow') newP.y = -10;
        Object.assign(p, newP);
      }

      // Draw
      ctx.fillStyle = `rgba(${p.color}, ${Math.max(0, p.alpha)})`;

      if (this.type === 'rain') {
        ctx.strokeStyle = `rgba(${p.color}, ${p.alpha})`;
        ctx.lineWidth = p.size;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x + p.vx * 2, p.y - p.length);
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }
}

// ─── SCREEN SHAKE ─────────────────────────────────

class ScreenShake {
  constructor() {
    this.intensity = 0;
    this.decay = 0.95;
  }

  trigger(intensity = 10) {
    this.intensity = intensity;
  }

  apply(ctx) {
    if (this.intensity > 0.5) {
      const dx = (Math.random() - 0.5) * this.intensity;
      const dy = (Math.random() - 0.5) * this.intensity;
      ctx.translate(dx, dy);
      this.intensity *= this.decay;
    } else {
      this.intensity = 0;
    }
  }
}

// ─── VIGNETTE EFFECT ──────────────────────────────

class VignetteEffect {
  constructor(ctx, width, height, options = {}) {
    this.ctx = ctx;
    this.W = width;
    this.H = height;
    this.intensity = options.intensity || 0.4;
    this.breathe = options.breathe !== false;
  }

  draw(time) {
    const ctx = this.ctx;
    const cx = this.W / 2;
    const cy = this.H / 2;
    const radius = Math.max(this.W, this.H) * 0.7;
    const intensity = this.breathe
      ? this.intensity + Math.sin(time * 0.3) * 0.05
      : this.intensity;

    const grad = ctx.createRadialGradient(cx, cy, radius * 0.3, cx, cy, radius);
    grad.addColorStop(0, 'rgba(0, 0, 0, 0)');
    grad.addColorStop(1, `rgba(0, 0, 0, ${intensity})`);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, this.W, this.H);
  }
}

// ─── TEXT OVERLAY ─────────────────────────────────

class TextOverlay {
  constructor(ctx, options = {}) {
    this.ctx = ctx;
    this.font = options.font || 'bold 32px sans-serif';
    this.color = options.color || '#FFFFFF';
    this.shadowColor = options.shadowColor || 'rgba(0,0,0,0.5)';
    this.align = options.align || 'center';
  }

  draw(text, x, y, time, options = {}) {
    const ctx = this.ctx;
    const typing = options.typing || false;
    const fadeIn = options.fadeIn || false;

    let displayText = text;
    if (typing && time !== undefined) {
      const charsVisible = Math.floor(time * (options.typingSpeed || 15));
      displayText = text.substring(0, Math.min(charsVisible, text.length));
    }

    let alpha = 1;
    if (fadeIn && time !== undefined) {
      alpha = Math.min(1, time * 2);
    }

    ctx.save();
    ctx.font = this.font;
    ctx.textAlign = this.align;
    ctx.textBaseline = 'middle';

    // Shadow
    ctx.fillStyle = this.shadowColor;
    ctx.fillText(displayText, x + 2, y + 2);

    // Text
    ctx.fillStyle = this.color;
    ctx.globalAlpha = alpha;
    ctx.fillText(displayText, x, y);

    ctx.restore();
  }
}

// Export
if (typeof module !== 'undefined') {
  module.exports = { ParticleSystem, ScreenShake, VignetteEffect, TextOverlay };
}
