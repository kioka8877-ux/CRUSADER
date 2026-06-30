/**
 * BetaMain.jsx — Composition principale CRUSADER Beta (v2 – sinusoidal camera)
 *
 * Passe l'intégralité de la timeline et du style au WorldScene sinusoïdal.
 * Plus de Sequences individuelles — un seul WorldScene gère tout.
 */
import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Background } from "./components/Background";
import { WorldScene } from "./components/WorldScene";

export const BetaMain = ({ timing, roadmap }) => {
  return (
    <AbsoluteFill>
      <Background style={roadmap.style} />
      <WorldScene timeline={roadmap.timeline} style={roadmap.style} />
      <Audio src={staticFile("audio_clean.mp3")} />
    </AbsoluteFill>
  );
};
