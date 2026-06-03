// src/components/Background.jsx — F03 SIGISMUND
// Fond permanent : couleur papier + grain animé (film grain) + vignette.
// Google Fonts est préchargé via delayRender/continueRender pour éviter
// que Remotion attende indéfiniment un @import réseau pendant le rendu.
import React, { useEffect, useRef } from "react";
import { AbsoluteFill, continueRender, delayRender, useCurrentFrame } from "remotion";

// Convertit un nom de police en slug Google Fonts (espaces → +)
const toGFSlug = (name) => name.trim().replace(/\s+/g, "+");

// Construit l'URL Google Fonts pour les deux polices configurées
const buildGoogleFontsUrl = (fontPrimary, fontAccent) => {
  const slugs = [...new Set([fontPrimary, fontAccent].map(toGFSlug))];
  const families = slugs
    .map((s) => `family=${s}:ital,wght@0,400;0,700;1,400;1,700`)
    .join("&");
  return `https://fonts.googleapis.com/css2?${families}&display=swap`;
};

export const Background = ({ style }) => {
  const frame = useCurrentFrame();

  // ── Google Fonts : chargement contrôlé via delayRender ───────────────────
  // On crée le handle une seule fois (useRef pour stabilité entre renders).
  const handleRef = useRef(null);
  if (handleRef.current === null) {
    handleRef.current = delayRender("Loading Google Fonts");
  }

  useEffect(() => {
    const handle = handleRef.current;
    const url = buildGoogleFontsUrl(style.font_primary, style.font_accent);

    // Vérifie si le lien existe déjà (idempotent entre renders)
    const existing = document.querySelector(`link[data-gfonts="${url}"]`);
    if (existing) {
      continueRender(handle);
      return;
    }

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = url;
    link.setAttribute("data-gfonts", url);
    // Timeout de sécurité : si Google Fonts ne répond pas en 8s, on continue quand même
    const fallback = setTimeout(() => continueRender(handle), 8000);
    link.onload = () => { clearTimeout(fallback); continueRender(handle); };
    link.onerror = () => { clearTimeout(fallback); continueRender(handle); };
    document.head.appendChild(link);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Grain animé : seed qui tourne toutes les 3 frames ────────────────────
  const grainSeed = Math.floor(frame / 3) % 64;
  const grainOpacity = style.grain_intensity ?? 0.15;

  return (
    <AbsoluteFill>
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
