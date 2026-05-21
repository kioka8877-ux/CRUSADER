// src/Main.jsx — F03 SIGISMUND
// Composition principale : Audio + Background + Séquences par segment.
import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Background } from "./components/Background";
import { Scene } from "./components/Scene";

export const Main = ({ timing, roadmap }) => {
  return (
    <AbsoluteFill>
      {/* Fond permanent (couleur + grain + vignette) */}
      <Background style={roadmap.style} />

      {/* Séquences — une par segment de roadmap */}
      {roadmap.timeline.map((seg, idx) => {
        const dur = seg.end_frame - seg.start_frame;
        if (dur <= 0) return null;

        // Correspondance 1-à-1 : timeline[idx] ↔ timing.segments[idx]
        const timingSeg = timing.segments[idx] || null;

        return (
          <Sequence
            key={seg.id}
            from={seg.start_frame}
            durationInFrames={dur}
            layout="none"
          >
            <Scene
              segment={seg}
              timingSeg={timingSeg}
              style={roadmap.style}
              durationInFrames={dur}
            />
          </Sequence>
        );
      })}

      {/* Piste audio */}
      <Audio src={staticFile("audio_clean.mp3")} />
    </AbsoluteFill>
  );
};
