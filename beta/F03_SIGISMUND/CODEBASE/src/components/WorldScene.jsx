import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TacticalArrow } from "./TacticalArrow";
import { WorldNode } from "./WorldNode";

const SPRING_CFG = { mass: 0.4, stiffness: 210, damping: 14 };
const PREVIEW_SCALE = 0.2;
const MARGIN = 24;
const EXIT_FRAMES = 12;

export const WorldScene = ({ segment, nextSegment, isTopRight, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // N enters with spring (0.2 → 1.0 scale)
  const enterSpring = spring({ frame, fps, config: SPRING_CFG });
  const enterScale = interpolate(enterSpring, [0, 1], [0.2, 1.0]);

  // N exits: last EXIT_FRAMES frames, shrinks toward preview corner
  const exitProgress = interpolate(
    frame,
    [durationInFrames - EXIT_FRAMES, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Preview corner geometry
  const previewW = width * PREVIEW_SCALE;
  const previewH = height * PREVIEW_SCALE;
  const cornerCX = width - MARGIN - previewW / 2;
  const cornerCY = isTopRight ? MARGIN + previewH / 2 : height - MARGIN - previewH / 2;

  // N translate toward corner on exit, scale down to 0.1
  const exitDX = (cornerCX - width / 2) * exitProgress;
  const exitDY = (cornerCY - height / 2) * exitProgress;
  const nScale = enterScale * interpolate(exitProgress, [0, 1], [1, 0.1]);

  const hasNext = !!nextSegment;
  const mediaType = segment.media_type || "image";
  const nextMediaType = nextSegment?.media_type || "image";

  return (
    <AbsoluteFill>
      {/* N — current segment */}
      <AbsoluteFill
        style={{
          transform: `translate(${exitDX}px, ${exitDY}px) scale(${nScale})`,
          transformOrigin: "center center",
        }}
      >
        <WorldNode imageFile={segment.image_file} mediaType={mediaType} />
      </AbsoluteFill>

      {/* N+1 — preview in corner (absent on last segment = fantôme) */}
      {hasNext && (
        <div
          style={{
            position: "absolute",
            width: previewW,
            height: previewH,
            [isTopRight ? "top" : "bottom"]: MARGIN,
            right: MARGIN,
            opacity: 0.2,
            borderRadius: 8,
            overflow: "hidden",
            boxShadow: "0 4px 24px rgba(0,0,0,0.9)",
          }}
        >
          <WorldNode imageFile={nextSegment.image_file} mediaType={nextMediaType} />
        </div>
      )}

      {/* Tactical arrow — center → corner */}
      {hasNext && (
        <TacticalArrow
          fromX={width / 2}
          fromY={height / 2}
          toX={cornerCX}
          toY={cornerCY}
        />
      )}
    </AbsoluteFill>
  );
};
