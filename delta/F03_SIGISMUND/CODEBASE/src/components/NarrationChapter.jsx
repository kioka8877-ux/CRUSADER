// src/components/NarrationChapter.jsx — F03 SIGISMUND (delta-test3)
// Rendu d'un chapitre narration : subset de la timeline gamma.
// Logique extraite de Main.jsx — identique, mais limitée à un range de segments.
//
// ── Utilisation ────────────────────────────────────────────────────────
// <NarrationChapter
//   timing={timing}
//   roadmap={roadmap}
//   segmentStartIdx={5}   // index de départ dans roadmap.timeline
//   segmentEndIdx={12}    // index de fin (exclusif)
// />
// ────────────────────────────────────────────────────────────────────────

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Background } from "./Background";
import { Scene } from "./Scene";

export const NarrationChapter = ({ timing, roadmap, segmentStartIdx, segmentEndIdx }) => {
  const { durationInFrames } = useVideoConfig();

  // Extraire les segments du chapitre
  const chapterSegments = roadmap.timeline.slice(segmentStartIdx, segmentEndIdx);
  if (chapterSegments.length === 0) return null;

  // Frame de départ du chapitre (dans le référentiel original)
  const chapterStartFrame = chapterSegments[0].start_frame;

  return (
    <AbsoluteFill>
      {/* Fond permanent (couleur + grain + vignette) */}
      <Background style={roadmap.style} />

      {/* Séquences — une par segment du chapitre.
          Les positions sont relatives au début du chapitre. */}
      {chapterSegments.map((seg, idx) => {
        const realIdx = segmentStartIdx + idx;
        const nextSeg = roadmap.timeline[realIdx + 1];
        // extendedEnd : début du segment suivant, ou fin du dernier segment du chapitre
        const isLastInChapter = idx === chapterSegments.length - 1;
        const extendedEnd = isLastInChapter
          ? seg.end_frame
          : (nextSeg ? nextSeg.start_frame : seg.end_frame);
        const dur = extendedEnd - seg.start_frame;
        if (dur <= 0) return null;

        // Position relative au début du chapitre
        const relativeStart = seg.start_frame - chapterStartFrame;

        // Correspondance 1-à-1 : timeline[realIdx] ↔ timing.segments[realIdx]
        const timingSeg = timing.segments[realIdx] || null;

        return (
          <Sequence
            key={seg.id}
            from={relativeStart}
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
    </AbsoluteFill>
  );
};
