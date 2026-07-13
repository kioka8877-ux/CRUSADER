import React from "react";
import { AbsoluteFill, Img, useCurrentFrame } from "remotion";

const FONT_FACES = `
  @font-face {
    font-family: 'Cinzel';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Cinzel-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Cinzel';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Cinzel-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 400;
    font-style: italic;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-Italic.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Lato';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Lato-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Lato';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Lato-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Oswald';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Oswald-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Oswald';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Oswald-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Roboto Slab';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/RobotoSlab-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Inter';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Inter-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Inter';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Inter-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Arial Black';
    font-weight: 900;
    font-style: normal;
    font-display: swap;
    src: local('Arial Black');
  }
`;

export const Background = ({ style }) => {
  const frame = useCurrentFrame();
  const grainSeed = Math.floor(frame / 3) % 64;
  const grainOpacity = style.grain_intensity ?? 0.15;

  return (
    <AbsoluteFill>
      <style>{FONT_FACES}</style>

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
