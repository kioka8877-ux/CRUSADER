/**
 * WorldScene.jsx — Sinusoidal Camera (v2 – spec beta-test3)
 *
 * Tous les worlds sont positionnés sur une courbe sinusoïdale.
 * La caméra voyage le long de cette courbe, se pause sur chaque world,
 * puis transite vers le suivant avec un easing Bézier.
 *
 * Paramètres configurables via roadmap.style :
 *   world_scale        – taille des visuels (0.0–1.0, défaut 0.70)
 *   world_opacity      – opacité des visuels actifs (défaut 1.0)
 *   camera_amplitude   – amplitude verticale de la sinusoïde (px, défaut 200)
 *   camera_spacing     – espacement horizontal entre worlds (px, défaut 1500)
 */
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { WorldNode } from "./WorldNode";

/* ── Bézier cubique easeInOut ── caméra uniquement ── */
const BEZIER_EASE = Easing.bezier(0.42, 0, 0.58, 1);

export const WorldScene = ({ timeline, style }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  /* ── Style params avec défauts ── */
  const worldScale = style.world_scale ?? 0.70;
  const worldOpacity = style.world_opacity ?? 1.0;
  const camAmplitude = style.camera_amplitude ?? 200;
  const camSpacing = style.camera_spacing ?? 1500;

  /* ── Dimensions d'un world ── */
  const wW = width * worldScale;
  const wH = height * worldScale;

  /* ── Position de chaque world sur la sinusoïde ── */
  /*    cos(i·π) alterne : +amp, -amp, +amp, -amp...   */
  const worldPositions = timeline.map((_, i) => ({
    x: i * camSpacing,
    y: camAmplitude * Math.cos(i * Math.PI),
  }));

  /* ── Trouver le segment actif ── */
  let segIdx = 0;
  for (let i = timeline.length - 1; i >= 0; i--) {
    if (frame >= timeline[i].start_frame) {
      segIdx = i;
      break;
    }
  }

  const seg = timeline[segIdx];
  const nextSeg = timeline[segIdx + 1] || null;
  const segEnd = nextSeg ? nextSeg.start_frame : durationInFrames;
  const tf = seg.trans_frames || 12;
  const transStart = segEnd - tf;

  /* ── Camera progress (index flottant le long de la courbe) ── */
  let cameraProgress = segIdx;

  if (frame >= transStart && nextSeg) {
    const rawT = interpolate(
      frame,
      [transStart, segEnd],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    cameraProgress = segIdx + BEZIER_EASE(rawT);
  }

  /* ── Position caméra sur la sinusoïde ── */
  const cameraX = cameraProgress * camSpacing;
  const cameraY = camAmplitude * Math.cos(cameraProgress * Math.PI);

  /* ── Translation du container (centre la caméra dans le viewport) ── */
  const translateX = width / 2 - cameraX;
  const translateY = height / 2 - cameraY;

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          transform: `translate(${translateX}px, ${translateY}px)`,
          willChange: "transform",
        }}
      >
        {timeline.map((s, i) => {
          const pos = worldPositions[i];
          const mediaType = s.media_type || "image";

          /* Opacité basée sur la distance à la caméra */
          const distance = Math.abs(i - cameraProgress);
          const distOpacity = Math.max(0, Math.min(1, 1.5 - distance));

          return (
            <div
              key={s.id}
              style={{
                position: "absolute",
                left: pos.x - wW / 2,
                top: pos.y - wH / 2,
                width: wW,
                height: wH,
                opacity: distOpacity * worldOpacity,
                borderRadius: 8,
                overflow: "hidden",
                boxShadow:
                  distOpacity > 0.3
                    ? "0 4px 24px rgba(0,0,0,0.5)"
                    : "none",
              }}
            >
              <WorldNode imageFile={s.image_file} mediaType={mediaType} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
