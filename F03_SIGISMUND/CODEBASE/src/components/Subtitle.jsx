// src/components/Subtitle.jsx — F03 SIGISMUND
// Rendu des sous-titres. Mots forts (is_strong) en police accent + couleur dorée.
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

// Constantes de fondu entrée / sortie (en frames)
const FADE_FRAMES = 4;

export const Subtitle = ({ segment, timingSeg, style, durationInFrames }) => {
  const frame = useCurrentFrame();

  // ── Fondu in/out ───────────────────────────────────────────────────────────
  const opacity = interpolate(
    frame,
    [0, FADE_FRAMES, durationInFrames - FADE_FRAMES, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // ── Position verticale ─────────────────────────────────────────────────────
  const posStyle = {};
  switch (style.subtitle_position) {
    case "top":
      posStyle.top = "8%";
      break;
    case "center":
      posStyle.top = "50%";
      posStyle.transform = "translateY(-50%)";
      break;
    default: // bottom
      posStyle.bottom = "8%";
  }

  // ── Rendu des mots (avec surlignage des mots forts) ───────────────────────
  const words = timingSeg?.words || [];

  const renderWords = () => {
    if (!words.length) {
      // Fallback : texte brut en police principale
      return (
        <span
          style={{
            fontFamily: `'${style.font_primary}', Georgia, serif`,
            color: style.subtitle_color,
          }}
        >
          {segment.text_subtitles}
        </span>
      );
    }

    return words.map((w, i) => (
      <React.Fragment key={i}>
        <span
          style={{
            fontFamily: w.is_strong
              ? `'${style.font_accent}', Georgia, serif`
              : `'${style.font_primary}', Georgia, serif`,
            fontStyle: w.is_strong ? "italic" : "normal",
            color: w.is_strong ? style.accent_color : style.subtitle_color,
          }}
        >
          {w.word}
        </span>
        {" "}
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
        textAlign: "center",
        opacity,
        ...posStyle,
      }}
    >
      <div
        style={{
          fontSize: style.subtitle_size,
          lineHeight: 1.25,
          textShadow: "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
          wordBreak: "break-word",
        }}
      >
        {renderWords()}
      </div>
    </div>
  );
};
