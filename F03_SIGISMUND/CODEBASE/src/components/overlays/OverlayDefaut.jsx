// overlays/OverlayDefaut.jsx — Poussière ambiante (fallback universel)
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

const MOTES = Array.from({ length: 8 }, (_, i) => ({
  id: i,
  x:     (i * 53 + 12) % 90 + 5,
  y:     (i * 31 + 8)  % 85 + 5,
  delay: (i * 29) % 100,
  speed: 0.03 + (i % 4) * 0.01,
  size:  2 + (i % 2),
}));

export function OverlayDefaut({ intensite, frame, fps }) {
  const baseOpacity = [0, 0.06, 0.1, 0.15][intensite] || 0.1;
  const cycleFps = fps * 6;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {MOTES.map(m => {
        const t = ((frame * m.speed + m.delay) % cycleFps) / cycleFps;
        // Dérive verticale lente
        const yOff = interpolate(t, [0, 0.5, 1], [0, -8, 0], { extrapolateRight: "clamp" });
        // Pulsation d'opacité
        const opPulse = interpolate(t, [0, 0.5, 1], [0.4, 1.0, 0.4], { extrapolateRight: "clamp" });
        return (
          <div key={m.id} style={{
            position: "absolute",
            left: `${m.x}%`,
            top: `calc(${m.y}% + ${yOff}px)`,
            width: `${m.size}px`,
            height: `${m.size}px`,
            borderRadius: "50%",
            background: "rgba(220, 215, 200, 0.8)",
            opacity: baseOpacity * opPulse,
          }} />
        );
      })}
    </AbsoluteFill>
  );
}
