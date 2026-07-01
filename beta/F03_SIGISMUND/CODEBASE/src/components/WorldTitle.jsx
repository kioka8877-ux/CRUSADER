/**
 * WorldTitle.jsx — Titre animé avec alternance top/right
 *
 * Rotation stricte :
 *   index pair  → titre EN HAUT, tombe du dessus (drop-Y)
 *   index impair → titre À DROITE, glisse depuis la droite (slide-X)
 *
 * Paramètres depuis roadmap.style :
 *   world_title_visible  – true/false (défaut false)
 *   world_title_font     – police (défaut font_primary)
 *   world_title_size     – taille px (défaut 28)
 *   world_title_color    – couleur (défaut "#FFFFFF")
 *   world_title_speed    – frames d'animation (défaut 12 ≈ 400ms@30fps)
 *
 * Données depuis segment.world_title (string). Si absent → rien affiché.
 */
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const WorldTitle = ({ segment, style, index = 0 }) => {
  const frame = useCurrentFrame();
  const visible = style.world_title_visible ?? false;
  const title = segment.world_title;

  if (!visible || !title) return null;

  const font = style.world_title_font ?? style.font_primary ?? "Cinzel";
  const size = style.world_title_size ?? 28;
  const color = style.world_title_color ?? "#FFFFFF";
  const speed = style.world_title_speed ?? 12;

  /* —— Animation locale (depuis le début du segment) —— */
  const segStart = segment.start_frame ?? 0;
  const localFrame = frame - segStart;

  const progress = interpolate(localFrame, [0, speed], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // smoothstep easing
  const eased = progress * progress * (3 - 2 * progress);

  /* —— Alternance : pair = top/drop, impair = right/slide —— */
  const isTop = index % 2 === 0;

  let posStyle, transform;

  if (isTop) {
    const dropY = interpolate(eased, [0, 1], [-60, 0]);
    posStyle = { top: 20, left: 0, right: 0, textAlign: "center" };
    transform = `translateY(${dropY}px)`;
  } else {
    const slideX = interpolate(eased, [0, 1], [80, 0]);
    posStyle = { top: 20, right: 24, textAlign: "right" };
    transform = `translateX(${slideX}px)`;
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
      }}
    >
      {title}
    </div>
  );
};
