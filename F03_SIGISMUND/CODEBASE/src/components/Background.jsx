// src/components/Background.jsx — F03 SIGISMUND
// Fond permanent : couleur papier + grain animé (film grain) + vignette.
import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

// Chargement Google Fonts (Cinzel + Playfair Display)
const GOOGLE_FONTS_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&display=swap');
`;

export const Background = ({ style }) => {
  const frame = useCurrentFrame();

  // ── Grain animé : seed qui tourne toutes les 3 frames ────────────────────
  const grainSeed = Math.floor(frame / 3) % 64;
  const grainOpacity = style.grain_intensity ?? 0.15;

  return (
    <AbsoluteFill>
      {/* Injection Google Fonts */}
      <style>{GOOGLE_FONTS_CSS}</style>

      {/* Couleur de fond */}
      <AbsoluteFill style={{ backgroundColor: style.background_color }} />

      {/* Grain (film grain via SVG feTurbulence) */}
      {grainOpacity > 0 && (
        <AbsoluteFill
          style={{
            opacity: grainOpacity,
            mixBlendMode: "overlay",
            pointerEvents: "none",
          }}
        >
          <svg
            width="100%"
            height="100%"
            xmlns="http://www.w3.org/2000/svg"
            style={{ display: "block" }}
          >
            <filter id={`grain-${grainSeed}`}>
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.75"
                numOctaves="4"
                seed={grainSeed}
                stitchTiles="stitch"
              />
              <feColorMatrix type="saturate" values="0" />
            </filter>
            <rect
              width="100%"
              height="100%"
              filter={`url(#grain-${grainSeed})`}
            />
          </svg>
        </AbsoluteFill>
      )}

      {/* Vignette */}
      {style.vignette && (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.70) 100%)",
            pointerEvents: "none",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
