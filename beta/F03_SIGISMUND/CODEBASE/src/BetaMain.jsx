import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { Background } from "./components/Background";
import { WorldScene } from "./components/WorldScene";

export const BetaMain = ({ timing, roadmap }) => {
  const { durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Background style={roadmap.style} />

      {roadmap.timeline.map((seg, idx) => {
        const nextSeg = roadmap.timeline[idx + 1] || null;
        const extendedEnd = nextSeg ? nextSeg.start_frame : durationInFrames;
        const dur = extendedEnd - seg.start_frame;
        if (dur <= 0) return null;

        // Strict alternance top-right / bottom-right — jamais même coin deux fois
        const isTopRight = idx % 2 === 0;

        return (
          <Sequence
            key={seg.id}
            from={seg.start_frame}
            durationInFrames={dur}
            layout="none"
          >
            <WorldScene
              segment={seg}
              nextSegment={nextSeg}
              isTopRight={isTopRight}
              durationInFrames={dur}
            />
          </Sequence>
        );
      })}

      <Audio src={staticFile("audio_clean.mp3")} />
    </AbsoluteFill>
  );
};
