/**
 * WorldTitle.jsx — Titre/label affiché sur chaque world
 *
 * Paramètres depuis roadmap.style :
 *   world_title_visible   – true/false (défaut false)
 *   world_title_position  – "left" / "right" (défaut "left")
 *   world_title_font      – police (défaut font_primary du style)
 *   world_title_size      – taille en px (défaut 28)
 *   world_title_color     – couleur (défaut "#FFFFFF")
 *
 * Données depuis segment.world_title (string). Si absent → rien affiché.
 */
import React from "react";

export const WorldTitle = ({ segment, style }) => {
  const visible = style.world_title_visible ?? false;
  const title = segment.world_title;

  if (!visible || !title) return null;

  const position = style.world_title_position ?? "left";
  const font = style.world_title_font ?? style.font_primary ?? "Cinzel";
  const size = style.world_title_size ?? 28;
  const color = style.world_title_color ?? "#FFFFFF";

  const posStyle =
    position === "right"
      ? { right: 24, textAlign: "right" }
      : { left: 24, textAlign: "left" };

  return (
    <div
      style={{
        position: "absolute",
        top: 20,
        ...posStyle,
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
