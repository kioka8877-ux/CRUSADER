/**
 * BetaSubtitle.jsx — Sous-titres pour la version Beta
 *
 * Affiche le sous-titre du segment actif basé sur le frame courant.
 * Tous les paramètres lus depuis roadmap.style :
 *
 *   subtitle_font     – police (défaut font_primary)
 *   subtitle_size     – taille px (défaut 44)
 *   subtitle_color    – couleur texte (défaut "#FFFFFF")
 *   subtitle_position – "top" / "center" / "bottom" (défaut "bottom")
 *   subtitle_align    – "left" / "center" / "right" (défaut "center")
 *   subtitle_anim     – animation fade in/out (défaut true)
 *   subtitle_anim_speed – frames de transition (défaut 5)
 *   accent_color      – couleur mots forts (défaut "#FFD700")
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const BetaSubtitle = ({ timeline, style, timing }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  /* ── Trouver le segment actif ── */
  let segIdx = 0;
  for (let i = timeline.length - 1; i >= 0; i--) {
    if (frame >= timeline[i].start_frame) {
      segIdx = i;
      break;
    }
  }

  const seg = timeline[segIdx];
  const text = seg.text_subtitles;
  if (!text) return null;

  /* ── Paramètres de style ── */
  const font = style.subtitle_font ?? style.font_primary ?? "Cinzel";
  const size = parseInt(style.subtitle_size, 10) || 44;
  const color = style.subtitle_color ?? "#FFFFFF";
  const accentColor = style.accent_color ?? "#FFD700";
  const position = style.subtitle_position ?? "bottom";
  const align = style.subtitle_align ?? "center";
  const animEnabled = style.subtitle_anim !== false;
  const fadeFrames = style.subtitle_anim_speed ?? 5;

  /* ── Durée locale du segment ── */
  const nextSeg = timeline[segIdx + 1] || null;
  const segEnd = nextSeg ? nextSeg.start_frame : durationInFrames;
  const localFrame = frame - seg.start_frame;
  const segDuration = segEnd - seg.start_frame;

  /* ── Fade in/out ── */
  const opacity = animEnabled
    ? interpolate(
        localFrame,
        [0, fadeFrames, segDuration - fadeFrames, segDuration],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 1;

  /* ── Slide in ── */
  const slideX = animEnabled
    ? interpolate(localFrame, [0, fadeFrames], [-30, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  /* ── Position verticale ── */
  const posStyle = {};
  switch (position) {
    case "top":
      posStyle.top = "8%";
      break;
    case "center":
      posStyle.top = "50%";
      posStyle.transform = `translateY(-50%) translateX(${slideX}px)`;
      break;
    default:
      posStyle.bottom = "8%";
  }

  const transformVal =
    position === "center"
      ? posStyle.transform
      : `translateX(${slideX}px)`;

  /* ── Rendu des mots (mots forts via timing si dispo) ── */
  const timingSeg = timing?.segments?.[segIdx];
  const words = timingSeg?.words || [];

  const renderText = () => {
    if (!words.length) {
      return (
        <span
          style={{
            fontFamily: `'${font}', Georgia, serif`,
            color,
          }}
        >
          {text}
        </span>
      );
    }

    return words.map((w, i) => (
      <React.Fragment key={i}>
        <span
          style={{
            fontFamily: `'${font}', Georgia, serif`,
            color: w.is_strong ? accentColor : color,
          }}
        >
          {w.word}
        </span>{" "}
      </React.Fragment>
    ));
  };

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        padding: "0 64px",
        textAlign: align,
        opacity,
        transform: transformVal,
        ...posStyle,
      }}
    >
      <div
        style={{
          fontSize: size,
          lineHeight: 1.25,
          textShadow:
            "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
          wordBreak: "break-word",
        }}
      >
        {renderText()}
      </div>
    </div>
  );
};
