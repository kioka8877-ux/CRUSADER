/**
 * WorldTitle.jsx — Titre animé avec alternance top/right
 * PREVIEW MODE — copie conforme de F03, auto-suffisant
 */
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const WorldTitle = ({ segment, style, index = 0, worldW = 0, worldH = 0 }) => {
  const frame = useCurrentFrame();
  const visible = style.world_title_visible ?? false;

  const title = segment.world_title
    || (segment.text_subtitles ? segment.text_subtitles.split(" ").slice(0, 4).join(" ") : null);

  if (!visible || !title) return null;

  const font = style.world_title_font ?? style.font_primary ?? "Cinzel";
  const size = style.world_title_size ?? 28;
  const color = style.world_title_color ?? "#FFFFFF";
  const speed = style.world_title_speed ?? 12;
  const gap = style.world_title_gap ?? 20;

  const segStart = segment.start_frame ?? 0;
  const localFrame = frame - segStart;

  const progress = interpolate(localFrame, [0, speed], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const eased = progress * progress * (3 - 2 * progress);

  const isAbove = index % 2 === 0;

  let posStyle, transform;

  if (isAbove) {
    const dropY = interpolate(eased, [0, 1], [-40, 0]);
    posStyle = {
      top: -(gap + size + 4),
      left: 0,
      right: 0,
      textAlign: "center",
    };
    transform = `translateY(${dropY}px)`;
  } else {
    const slideX = interpolate(eased, [0, 1], [50, 0]);
    posStyle = {
      left: worldW + gap,
      top: worldH / 2,
    };
    transform = `translateY(-50%) translateX(${slideX}px)`;
  }

  return (
    <div
      style={{
        position: "absolute",
        ...posStyle,
        transform,
        opacity: eased,
        fontFamily: `'${font}', Georgia, serif`,
        fontSize: size,
        color,
        textShadow: "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
        pointerEvents: "none",
        zIndex: 10,
        whiteSpace: "nowrap",
      }}
    >
      {title}
    </div>
  );
};
