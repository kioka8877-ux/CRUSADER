// src/components/Scene.jsx — F03 SIGISMUND
// Rendu d'un segment : image (Ken Burns) + sous-titre.
import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Subtitle } from "./Subtitle";

export const Scene = ({ segment, timingSeg, style, durationInFrames }) => {
  const frame = useCurrentFrame();

  // ── Ken Burns : très léger zoom + dérive horizontale ──────────────────────
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateX = interpolate(frame, [0, durationInFrames], [0, -10], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      {/* Image de fond du segment */}
      {segment.image_file && (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img
            src={staticFile(`images/${segment.image_file}`)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${scale}) translateX(${translateX}px)`,
              transformOrigin: "center center",
            }}
          />
        </AbsoluteFill>
      )}

      {/* Sous-titre */}
      <Subtitle
        segment={segment}
        timingSeg={timingSeg}
        style={style}
        durationInFrames={durationInFrames}
      />
    </AbsoluteFill>
  );
};
