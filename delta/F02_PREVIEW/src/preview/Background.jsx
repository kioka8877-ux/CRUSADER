/**
 * Background.jsx — PREVIEW MODE
 * Pas de staticFile() — chemins relatifs "./" pour export HTML
 * Polices en local() fallback (pas de woff2 en preview)
 */
import React from "react";
import { AbsoluteFill, Img, useCurrentFrame } from "remotion";

export const Background = ({ style }) => {
  const frame = useCurrentFrame();
  const grainSeed = Math.floor(frame / 3) % 64;
  const grainOpacity = style.grain_intensity ?? 0.15;

  return (
    <AbsoluteFill>
      {style.background_image && style.background_image !== "solid" ? (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img
            src={"./" + style.background_image}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${style.background_scale ?? 1})`,
              transformOrigin: "center center",
            }}
          />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ backgroundColor: style.background_color }} />
      )}

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
