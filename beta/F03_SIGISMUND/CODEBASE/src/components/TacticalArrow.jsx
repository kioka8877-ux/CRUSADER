import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

const SPRING_CFG = { mass: 0.4, stiffness: 210, damping: 14 };

export const TacticalArrow = ({ fromX, fromY, toX, toY }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame, fps, config: SPRING_CFG });

  // Arrow grows from origin to target as spring settles
  const endX = fromX + (toX - fromX) * progress;
  const endY = fromY + (toY - fromY) * progress;

  return (
    <svg
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        overflow: "visible",
        pointerEvents: "none",
      }}
    >
      <defs>
        <marker
          id="beta-head"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#FF1A1A" />
        </marker>
      </defs>
      <line
        x1={fromX}
        y1={fromY}
        x2={endX}
        y2={endY}
        stroke="#FF1A1A"
        strokeWidth={5}
        strokeOpacity={progress}
        markerEnd="url(#beta-head)"
      />
    </svg>
  );
};
