/**
 * WorldScene.jsx — Style sinusoïdal (spec verrouillée 22/06)
 *
 * World canvas pré-baked :
 *   - Caméra voyage via Bézier cubique easeInOut (PAS spring)
 *   - N plein cadre, reste en place — la caméra le quitte
 *   - N+1 minuscule teaser, alterne strict haut-droit / bas-droit
 *   - trans_frames lu depuis roadmap.json (8/12/18/30)
 *   - Seuil terminal fantôme (dernier visuel reste)
 *   - Spring réservé à la marque (TacticalArrow), pas à la caméra
 */
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TacticalArrow } from "./TacticalArrow";
import { WorldNode } from "./WorldNode";

/* ── Bézier cubique easeInOut ── caméra uniquement ── */
const BEZIER_EASE = Easing.bezier(0.42, 0, 0.58, 1);

/* ── Teaser N+1 — minuscule ── */
const TEASER_RATIO = 0.12; // 12 % du viewport
const MARGIN = 28;
const TOP_Y_RATIO = 0.08; // haut-droit — niveau titre
const BOT_Y_RATIO = 0.82; // bas-droit — sous le sous-titre

export const WorldScene = ({
  segment,
  nextSegment,
  isTopRight,
  durationInFrames,
  transFrames,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const tf = transFrames || 12;
  const transStart = durationInFrames - tf;

  /* ── Camera travel — Bézier cubique easeInOut ── */
  const rawT = interpolate(
    frame,
    [transStart, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const t = BEZIER_EASE(rawT);

  /* ── Teaser corner geometry ── */
  const tW = width * TEASER_RATIO;
  const tH = height * TEASER_RATIO;
  const tX = width - MARGIN - tW;
  const tY = isTopRight ? height * TOP_Y_RATIO : height * BOT_Y_RATIO;
  const tCX = tX + tW / 2;
  const tCY = tY + tH / 2;

  const hasNext = !!nextSegment;
  const mediaType = segment.media_type || "image";
  const nextMediaType = nextSegment?.media_type || "image";

  /* ── N — visuel actif : reste en place, la caméra le quitte ── */
  const nScale = interpolate(t, [0, 1], [1, 0.55]);
  const nOpacity = interpolate(t, [0, 0.5, 1], [1, 0.85, 0]);

  /* ── N+1 — teaser minuscule → plein cadre ── */
  const n1Left = interpolate(t, [0, 1], [tX, 0]);
  const n1Top = interpolate(t, [0, 1], [tY, 0]);
  const n1Width = interpolate(t, [0, 1], [tW, width]);
  const n1Height = interpolate(t, [0, 1], [tH, height]);
  const n1Opacity = interpolate(t, [0, 0.2, 1], [0.2, 0.6, 1]);
  const n1Radius = interpolate(t, [0, 1], [6, 0]);

  return (
    <AbsoluteFill>
      {/* ── N — plein cadre → recule pendant le vol ── */}
      <AbsoluteFill
        style={{
          transform: `scale(${nScale})`,
          opacity: nOpacity,
          transformOrigin: "center center",
        }}
      >
        <WorldNode imageFile={segment.image_file} mediaType={mediaType} />
      </AbsoluteFill>

      {/* ── N+1 — teaser minuscule → plein cadre (fantôme si dernier) ── */}
      {hasNext && (
        <div
          style={{
            position: "absolute",
            left: n1Left,
            top: n1Top,
            width: n1Width,
            height: n1Height,
            opacity: n1Opacity,
            borderRadius: n1Radius,
            overflow: "hidden",
            boxShadow: t < 0.5 ? "0 2px 16px rgba(0,0,0,0.85)" : "none",
          }}
        >
          <WorldNode
            imageFile={nextSegment.image_file}
            mediaType={nextMediaType}
          />
        </div>
      )}

      {/* ── Marque — ligne tracée pendant le vol, spring uniquement ── */}
      {hasNext && (
        <TacticalArrow
          fromX={width / 2}
          fromY={height / 2}
          toX={tCX}
          toY={tCY}
          transStart={transStart}
          transFrames={tf}
        />
      )}
    </AbsoluteFill>
  );
};
