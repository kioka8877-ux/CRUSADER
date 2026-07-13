/**
 * BetaMain.jsx — Composition principale CRUSADER Beta (v2.1 – sinusoidal camera)
 * PREVIEW MODE : Audio retiré (pas d'audio en preview)
 * Auto-suffisant — ne dépend pas de F03
 */
import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "./Background";
import { WorldScene } from "./WorldScene";
import { BetaSubtitle } from "./BetaSubtitle";

export const BetaMain = ({ timing, roadmap }) => {
  return (
    <AbsoluteFill>
      <Background style={roadmap.style} />
      <WorldScene timeline={roadmap.timeline} style={roadmap.style} />
      <BetaSubtitle
        timeline={roadmap.timeline}
        style={roadmap.style}
        timing={timing}
      />
    </AbsoluteFill>
  );
};
