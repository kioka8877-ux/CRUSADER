/**
 * WorldScene.jsx — Sinusoidal Camera (v2.1 – spec beta-test3)
 * PREVIEW MODE — copie conforme de F03, auto-suffisant
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
import { WorldTitle } from "./WorldTitle";

const BEZIER_EASE = Easing.bezier(0.42, 0, 0.58, 1);

export const WorldScene = ({ timeline, style }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const worldScale = style.world_scale ?? 0.70;
  const worldNextScale = style.world_next_scale ?? worldScale * 0.5;
  const worldOpacity = style.world_opacity ?? 1.0;
  const worldNextOpacity = style.world_next_opacity ?? 0.3;
  const camAmplitude = style.camera_amplitude ?? 200;
  const camSpacing = style.camera_spacing ?? 1500;

  const worldPositions = timeline.map((_, i) => ({
    x: i * camSpacing,
    y: camAmplitude * Math.cos(i * Math.PI),
  }));

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

  const cameraX = cameraProgress * camSpacing;
  const cameraY = camAmplitude * Math.cos(cameraProgress * Math.PI);

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

          const distance = Math.abs(i - cameraProgress);
          const t = Math.min(distance, 1);

          const thisScale = worldScale + (worldNextScale - worldScale) * t;
          const thisOpacity =
            (worldOpacity + (worldNextOpacity - worldOpacity) * t) *
            Math.max(0, Math.min(1, 1.5 - distance));

          const wW = width * thisScale;
          const wH = height * thisScale;

          if (thisOpacity <= 0) return null;

          return (
            <div
              key={s.id}
              style={{
                position: "absolute",
                left: pos.x - wW / 2,
                top: pos.y - wH / 2,
                width: wW,
                height: wH,
                opacity: thisOpacity,
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  borderRadius: 8,
                  overflow: "hidden",
                  boxShadow:
                    thisOpacity > 0.3
                      ? "0 4px 24px rgba(0,0,0,0.5)"
                      : "none",
                }}
              >
                <WorldNode imageFile={s.image_file} mediaType={mediaType} />
              </div>
              <WorldTitle segment={s} style={style} index={i} worldW={wW} worldH={wH} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
