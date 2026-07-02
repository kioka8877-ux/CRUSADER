/**
 * CRUSADER Delta — F03A L'INTERPRÉTEUR
 * characters.js
 *
 * Personnage paramétrique Canvas 2D avec :
 * - Corps articulé (tête, torse, bras, jambes avec articulations)
 * - Système de postures (idle, walk, talk, gesture, sit)
 * - Émotions faciales (neutral, happy, sad, angry, surprised, thinking)
 * - 12 principes d'animation Disney intégrés
 *
 * Usage:
 *   const char = new CrusaderCharacter(ctx, { scale: 1, palette: {...} });
 *   char.setState('walk', 'happy');
 *   char.draw(x, y, time);
 */

class CrusaderCharacter {
  constructor(ctx, options = {}) {
    this.ctx = ctx;
    this.scale = options.scale || 1;
    this.palette = {
      skin: options.palette?.skin || '#F4C280',
      outline: options.palette?.outline || '#2C3E50',
      hair: options.palette?.hair || '#34495E',
      shirt: options.palette?.shirt || '#3498DB',
      pants: options.palette?.pants || '#2C3E50',
      shoes: options.palette?.shoes || '#1A1A2E',
      eye: options.palette?.eye || '#FFFFFF',
      pupil: options.palette?.pupil || '#2C3E50',
      mouth: options.palette?.mouth || '#C0392B',
      ...options.palette,
    };
    this.lineWidth = options.lineWidth || 3;
    this.posture = 'idle';
    this.emotion = 'neutral';
    this.direction = 1; // 1 = right, -1 = left
    this.transitionProgress = 1;
    this.prevPosture = 'idle';
  }

  setState(posture, emotion, direction) {
    if (posture && posture !== this.posture) {
      this.prevPosture = this.posture;
      this.posture = posture;
      this.transitionProgress = 0;
    }
    if (emotion) this.emotion = emotion;
    if (direction !== undefined) this.direction = direction;
  }

  // ─── 12 PRINCIPLES HELPERS ───────────────────────

  /** Principle 1: Squash & Stretch */
  _squashStretch(t, intensity = 0.08) {
    const s = Math.sin(t * 3) * intensity;
    return { sx: 1 - s, sy: 1 + s };
  }

  /** Principle 2: Anticipation — wind-up before action */
  _anticipation(t, phase, amount = 0.05) {
    if (phase < 0.15) return -amount * Math.sin((phase / 0.15) * Math.PI);
    return 0;
  }

  /** Principle 5: Follow-through & overlapping — delayed secondary motion */
  _followThrough(t, delay = 0.3) {
    return Math.sin((t - delay) * 2);
  }

  /** Principle 6: Slow in / Slow out — ease curve */
  _easeInOut(t) {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  /** Principle 7: Arcs — natural arc motion */
  _arc(t, radius = 5) {
    return Math.sin(t) * radius;
  }

  /** Principle 9: Timing — variable speed cycles */
  _timing(t, speed = 1) {
    return t * speed;
  }

  /** Principle 10: Exaggeration */
  _exaggerate(value, factor = 1.3) {
    return value * factor;
  }

  // ─── BODY SKELETON ──────────────────────────────

  _getSkeleton(time, posture) {
    const t = time;
    const s = this.scale;

    // Base skeleton (idle standing)
    const skeleton = {
      head: { x: 0, y: -70 * s, radius: 18 * s },
      neck: { x: 0, y: -52 * s },
      shoulderL: { x: -18 * s, y: -48 * s },
      shoulderR: { x: 18 * s, y: -48 * s },
      elbowL: { x: -28 * s, y: -28 * s },
      elbowR: { x: 28 * s, y: -28 * s },
      handL: { x: -30 * s, y: -8 * s },
      handR: { x: 30 * s, y: -8 * s },
      hip: { x: 0, y: -8 * s },
      hipL: { x: -10 * s, y: -6 * s },
      hipR: { x: 10 * s, y: -6 * s },
      kneeL: { x: -12 * s, y: 22 * s },
      kneeR: { x: 12 * s, y: 22 * s },
      footL: { x: -14 * s, y: 48 * s },
      footR: { x: 14 * s, y: 48 * s },
      torsoTop: { x: 0, y: -48 * s },
      torsoBottom: { x: 0, y: -8 * s },
    };

    // Apply posture-specific deformations
    switch (posture) {
      case 'walk':
        this._applyWalk(skeleton, t, s);
        break;
      case 'talk':
        this._applyTalk(skeleton, t, s);
        break;
      case 'gesture':
        this._applyGesture(skeleton, t, s);
        break;
      case 'sit':
        this._applySit(skeleton, t, s);
        break;
      case 'idle':
      default:
        this._applyIdle(skeleton, t, s);
        break;
    }

    return skeleton;
  }

  _applyIdle(sk, t, s) {
    // Principle 8: Secondary action — subtle breathing
    const breathe = Math.sin(t * 1.5) * 2 * s;
    sk.head.y += breathe * 0.5;
    sk.shoulderL.y += breathe * 0.3;
    sk.shoulderR.y += breathe * 0.3;
    sk.neck.y += breathe * 0.4;
    sk.torsoTop.y += breathe * 0.3;

    // Subtle arm sway
    sk.handL.x += Math.sin(t * 0.8) * 3 * s;
    sk.handR.x -= Math.sin(t * 0.8 + 0.5) * 3 * s;
    sk.elbowL.x += Math.sin(t * 0.8) * 1.5 * s;
    sk.elbowR.x -= Math.sin(t * 0.8 + 0.5) * 1.5 * s;
  }

  _applyWalk(sk, t, s) {
    const cycle = t * 3; // walk speed
    const stride = Math.sin(cycle) * 15 * s;
    const bounce = Math.abs(Math.sin(cycle)) * 4 * s;

    // Principle 1: Squash & stretch on bounce
    const { sy } = this._squashStretch(cycle, 0.03);

    // Legs — alternating stride
    sk.footL.x = -14 * s + stride;
    sk.footR.x = 14 * s - stride;
    sk.kneeL.x = -12 * s + stride * 0.5;
    sk.kneeR.x = 12 * s - stride * 0.5;
    sk.kneeL.y = 22 * s - Math.abs(Math.sin(cycle)) * 8 * s;
    sk.kneeR.y = 22 * s - Math.abs(Math.sin(cycle + Math.PI)) * 8 * s;
    sk.footL.y = 48 * s - Math.max(0, Math.sin(cycle)) * 12 * s;
    sk.footR.y = 48 * s - Math.max(0, Math.sin(cycle + Math.PI)) * 12 * s;

    // Body bounce
    sk.head.y -= bounce * sy;
    sk.neck.y -= bounce * 0.8;
    sk.torsoTop.y -= bounce * 0.7;
    sk.hip.y -= bounce * 0.3;

    // Principle 7: Arcs — arms swing in arcs
    sk.handL.x = -30 * s - stride * 0.6;
    sk.handR.x = 30 * s + stride * 0.6;
    sk.handL.y = -8 * s + this._arc(cycle, 5 * s);
    sk.handR.y = -8 * s + this._arc(cycle + Math.PI, 5 * s);
    sk.elbowL.x = -28 * s - stride * 0.3;
    sk.elbowR.x = 28 * s + stride * 0.3;

    // Principle 5: Follow-through — head lags slightly
    sk.head.x = Math.sin(cycle - 0.3) * 2 * s;
  }

  _applyTalk(sk, t, s) {
    this._applyIdle(sk, t, s);

    // Principle 8: Secondary action — hand gestures while talking
    const talkCycle = t * 4;
    sk.handR.x = 30 * s + Math.sin(talkCycle) * 10 * s;
    sk.handR.y = -25 * s + Math.sin(talkCycle * 1.3) * 8 * s;
    sk.elbowR.x = 28 * s + Math.sin(talkCycle) * 5 * s;
    sk.elbowR.y = -35 * s + Math.sin(talkCycle * 0.7) * 4 * s;
  }

  _applyGesture(sk, t, s) {
    this._applyIdle(sk, t, s);

    // Both arms up in expressive gesture
    const gestCycle = t * 2;
    const raise = this._easeInOut((Math.sin(gestCycle) + 1) / 2);

    sk.handL.x = -35 * s - raise * 10 * s;
    sk.handL.y = -40 * s - raise * 25 * s;
    sk.handR.x = 35 * s + raise * 10 * s;
    sk.handR.y = -40 * s - raise * 25 * s;
    sk.elbowL.x = -30 * s - raise * 5 * s;
    sk.elbowL.y = -40 * s - raise * 10 * s;
    sk.elbowR.x = 30 * s + raise * 5 * s;
    sk.elbowR.y = -40 * s - raise * 10 * s;

    // Slight body lean
    sk.head.y -= raise * 3 * s;
  }

  _applySit(sk, t, s) {
    // Seated posture
    sk.hip.y = 10 * s;
    sk.hipL.y = 12 * s;
    sk.hipR.y = 12 * s;
    sk.kneeL = { x: -20 * s, y: 15 * s };
    sk.kneeR = { x: 20 * s, y: 15 * s };
    sk.footL = { x: -22 * s, y: 40 * s };
    sk.footR = { x: 22 * s, y: 40 * s };
    sk.torsoBottom.y = 10 * s;

    // Breathing
    const breathe = Math.sin(t * 1.5) * 1.5 * s;
    sk.head.y += breathe * 0.3;
    sk.shoulderL.y += breathe * 0.2;
    sk.shoulderR.y += breathe * 0.2;
  }

  // ─── FACE / EMOTION ─────────────────────────────

  _drawFace(x, y, radius, time) {
    const ctx = this.ctx;
    const r = radius;
    const p = this.palette;

    // Head circle
    ctx.fillStyle = p.skin;
    ctx.strokeStyle = p.outline;
    ctx.lineWidth = this.lineWidth;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Hair (top of head)
    ctx.fillStyle = p.hair;
    ctx.beginPath();
    ctx.arc(x, y - r * 0.15, r * 1.05, Math.PI, Math.PI * 2);
    ctx.fill();

    // Eyes
    const eyeSpacing = r * 0.35;
    const eyeY = y - r * 0.1;
    const eyeR = r * 0.18;
    const pupilR = r * 0.09;

    // Eye whites
    ctx.fillStyle = p.eye;
    ctx.beginPath();
    ctx.ellipse(x - eyeSpacing, eyeY, eyeR, eyeR * 1.1, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = p.outline;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(x + eyeSpacing, eyeY, eyeR, eyeR * 1.1, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Pupils — with subtle look direction
    const lookX = Math.sin(time * 0.5) * pupilR * 0.3;
    ctx.fillStyle = p.pupil;
    ctx.beginPath();
    ctx.arc(x - eyeSpacing + lookX, eyeY, pupilR, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x + eyeSpacing + lookX, eyeY, pupilR, 0, Math.PI * 2);
    ctx.fill();

    // Emotion-specific features
    this._drawEmotion(x, y, r, time);
  }

  _drawEmotion(x, y, r, time) {
    const ctx = this.ctx;
    const mouthY = y + r * 0.35;
    const mouthW = r * 0.4;
    const eyeY = y - r * 0.1;
    const eyeSpacing = r * 0.35;
    const browY = y - r * 0.32;

    ctx.strokeStyle = this.palette.outline;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';

    switch (this.emotion) {
      case 'happy':
        // Smile
        ctx.beginPath();
        ctx.arc(x, mouthY - r * 0.05, mouthW, 0.1 * Math.PI, 0.9 * Math.PI);
        ctx.stroke();
        // Raised eyebrows
        ctx.beginPath();
        ctx.arc(x - eyeSpacing, browY + 2, r * 0.2, Math.PI * 1.2, Math.PI * 1.8);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x + eyeSpacing, browY + 2, r * 0.2, Math.PI * 1.2, Math.PI * 1.8);
        ctx.stroke();
        // Blush
        ctx.fillStyle = 'rgba(255, 150, 150, 0.3)';
        ctx.beginPath();
        ctx.ellipse(x - eyeSpacing - 2, mouthY - r * 0.15, r * 0.15, r * 0.08, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(x + eyeSpacing + 2, mouthY - r * 0.15, r * 0.15, r * 0.08, 0, 0, Math.PI * 2);
        ctx.fill();
        break;

      case 'sad':
        // Frown
        ctx.beginPath();
        ctx.arc(x, mouthY + r * 0.15, mouthW * 0.7, Math.PI * 1.2, Math.PI * 1.8);
        ctx.stroke();
        // Droopy eyebrows
        ctx.beginPath();
        ctx.moveTo(x - eyeSpacing - r * 0.15, browY - 2);
        ctx.lineTo(x - eyeSpacing + r * 0.15, browY + 3);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x + eyeSpacing + r * 0.15, browY - 2);
        ctx.lineTo(x + eyeSpacing - r * 0.15, browY + 3);
        ctx.stroke();
        break;

      case 'angry':
        // Tight mouth
        ctx.beginPath();
        ctx.moveTo(x - mouthW * 0.5, mouthY);
        ctx.lineTo(x + mouthW * 0.5, mouthY);
        ctx.stroke();
        // Angry V eyebrows
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(x - eyeSpacing - r * 0.18, browY - 4);
        ctx.lineTo(x - eyeSpacing + r * 0.1, browY + 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x + eyeSpacing + r * 0.18, browY - 4);
        ctx.lineTo(x + eyeSpacing - r * 0.1, browY + 2);
        ctx.stroke();
        break;

      case 'surprised':
        // O mouth
        ctx.fillStyle = this.palette.mouth;
        ctx.beginPath();
        ctx.ellipse(x, mouthY, mouthW * 0.35, mouthW * 0.45, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        // Raised eyebrows (high)
        ctx.beginPath();
        ctx.arc(x - eyeSpacing, browY - 4, r * 0.2, Math.PI * 1.2, Math.PI * 1.8);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x + eyeSpacing, browY - 4, r * 0.2, Math.PI * 1.2, Math.PI * 1.8);
        ctx.stroke();
        break;

      case 'thinking':
        // Side mouth
        ctx.beginPath();
        ctx.moveTo(x + mouthW * 0.1, mouthY);
        ctx.quadraticCurveTo(x + mouthW * 0.4, mouthY - 3, x + mouthW * 0.5, mouthY + 2);
        ctx.stroke();
        // One raised eyebrow
        ctx.beginPath();
        ctx.arc(x - eyeSpacing, browY, r * 0.2, Math.PI * 1.2, Math.PI * 1.8);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x + eyeSpacing, browY - 5, r * 0.2, Math.PI * 1.15, Math.PI * 1.85);
        ctx.stroke();
        break;

      case 'neutral':
      default:
        // Simple line mouth
        ctx.beginPath();
        ctx.moveTo(x - mouthW * 0.4, mouthY);
        ctx.quadraticCurveTo(x, mouthY + 2, x + mouthW * 0.4, mouthY);
        ctx.stroke();
        // Flat eyebrows
        ctx.beginPath();
        ctx.moveTo(x - eyeSpacing - r * 0.15, browY);
        ctx.lineTo(x - eyeSpacing + r * 0.15, browY);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x + eyeSpacing - r * 0.15, browY);
        ctx.lineTo(x + eyeSpacing + r * 0.15, browY);
        ctx.stroke();
        break;
    }
  }

  // ─── BODY DRAWING ───────────────────────────────

  _drawLimb(from, to, width, color) {
    const ctx = this.ctx;
    ctx.strokeStyle = color || this.palette.outline;
    ctx.lineWidth = width || this.lineWidth * 1.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
  }

  _drawBody(sk) {
    const ctx = this.ctx;
    const p = this.palette;

    // Torso — filled shape
    ctx.fillStyle = p.shirt;
    ctx.strokeStyle = p.outline;
    ctx.lineWidth = this.lineWidth;
    ctx.beginPath();
    ctx.moveTo(sk.shoulderL.x, sk.shoulderL.y);
    ctx.lineTo(sk.shoulderR.x, sk.shoulderR.y);
    ctx.lineTo(sk.hipR.x + 2, sk.torsoBottom.y);
    ctx.lineTo(sk.hipL.x - 2, sk.torsoBottom.y);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Legs
    this._drawLimb(sk.hipL, sk.kneeL, this.lineWidth * 2.2, p.pants);
    this._drawLimb(sk.hipR, sk.kneeR, this.lineWidth * 2.2, p.pants);
    this._drawLimb(sk.kneeL, sk.footL, this.lineWidth * 2, p.pants);
    this._drawLimb(sk.kneeR, sk.footR, this.lineWidth * 2, p.pants);

    // Shoes
    ctx.fillStyle = p.shoes;
    ctx.beginPath();
    ctx.ellipse(sk.footL.x, sk.footL.y, 7 * this.scale, 4 * this.scale, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(sk.footR.x, sk.footR.y, 7 * this.scale, 4 * this.scale, 0, 0, Math.PI * 2);
    ctx.fill();

    // Arms
    this._drawLimb(sk.shoulderL, sk.elbowL, this.lineWidth * 1.8, p.shirt);
    this._drawLimb(sk.shoulderR, sk.elbowR, this.lineWidth * 1.8, p.shirt);
    this._drawLimb(sk.elbowL, sk.handL, this.lineWidth * 1.5, p.skin);
    this._drawLimb(sk.elbowR, sk.handR, this.lineWidth * 1.5, p.skin);

    // Hands
    ctx.fillStyle = p.skin;
    ctx.beginPath();
    ctx.arc(sk.handL.x, sk.handL.y, 4.5 * this.scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(sk.handR.x, sk.handR.y, 4.5 * this.scale, 0, Math.PI * 2);
    ctx.fill();
  }

  // ─── MAIN DRAW ──────────────────────────────────

  draw(x, y, time) {
    const ctx = this.ctx;

    // Transition blending (Principle 6: Slow in/out)
    if (this.transitionProgress < 1) {
      this.transitionProgress = Math.min(1, this.transitionProgress + 0.05);
    }

    const skeleton = this._getSkeleton(time, this.posture);

    ctx.save();
    ctx.translate(x, y);
    ctx.scale(this.direction, 1);

    // Principle 1: Global squash & stretch
    const { sx, sy } = this._squashStretch(time, 0.02);
    ctx.scale(sx, sy);

    // Draw order: legs → body → arms → head (back to front)
    this._drawBody(skeleton);
    this._drawFace(
      skeleton.head.x,
      skeleton.head.y,
      skeleton.head.radius,
      time
    );

    // Neck
    this._drawLimb(skeleton.neck, skeleton.head, this.lineWidth * 1.2, this.palette.skin);

    ctx.restore();
  }
}

// Export for both browser and Node
if (typeof module !== 'undefined') module.exports = { CrusaderCharacter };
