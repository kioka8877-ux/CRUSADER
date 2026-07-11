// src/components/ThumbnailSequence.jsx — F03 SIGISMUND (delta-test3)
// Rendu d'une séquence miniature : pan/zoom 2D sur le PNG avec interpolation spring.
// La caméra virtuelle part de fromWaypoint (ou vue globale si null) et arrive sur toWaypoint.
//
// ── Waypoints ──────────────────────────────────────────────────────────
// Coordonnées normalisées 0-1 (x, y) relatives à l'image.
// Remotion recalcule en pixels réels selon width/height de la composition.
// ────────────────────────────────────────────────────────────────────────

import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// Zoom cible sur l'icône destination
const TARGET_ZOOM = 2.5;

export const ThumbnailSequence = ({
  thumbnailSrc,
  fromWaypoint,  // {x, y} normalisé 0-1, ou null = vue globale
  toWaypoint,    // {x, y} normalisé 0-1
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // ── Spring : mouvement fluide caméra ──────────────────────────────────
  const progress = spring({
    frame,
    fps,
    config: { mass: 0.4, stiffness: 210, damping: 14 },
    durationInFrames,
  });

  // ── Position caméra (normalisée 0-1) ──────────────────────────────────
  const fromX = fromWaypoint ? fromWaypoint.x : 0.5;
  const fromY = fromWaypoint ? fromWaypoint.y : 0.5;
  const toX   = toWaypoint.x;
  const toY   = toWaypoint.y;

  const camX = interpolate(progress, [0, 1], [fromX, toX]);
  const camY = interpolate(progress, [0, 1], [fromY, toY]);

  // ── Zoom : départ = zoom précédent (ou vue globale), arrivée = TARGET_ZOOM ──
  const fromScale = fromWaypoint ? TARGET_ZOOM : 1.0;
  const scale = interpolate(progress, [0, 1], [fromScale, TARGET_ZOOM]);

  // ── Translation pour centrer le point caméra ──────────────────────────
  // transform: translate(tx, ty) scale(S) avec transformOrigin: center center
  // tx = S * width  * (0.5 - camX)
  // ty = S * height * (0.5 - camY)
  const tx = scale * width  * (0.5 - camX);
  const ty = scale * height * (0.5 - camY);

  // ── Fondu enchaîné en début et fin de séquence ────────────────────────
  const FADE = 4; // frames
  const opacity = interpolate(
    frame,
    [0, FADE, durationInFrames - FADE, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img
        src={staticFile(thumbnailSrc)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          transform: `translate(${tx}px, ${ty}px) scale(${scale})`,
          transformOrigin: "center center",
          opacity,
        }}
      />
    </AbsoluteFill>
  );
};
