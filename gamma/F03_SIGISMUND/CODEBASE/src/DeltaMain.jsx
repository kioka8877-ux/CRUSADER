// src/DeltaMain.jsx — F03 SIGISMUND (delta-test3)
// Composition principale DELTA : timeline hybride miniature + narration.
//
// ── Principe ───────────────────────────────────────────────────────────
// Si roadmap.thumbnail_plan est présent, la timeline devient :
//
//   [ThumbSeq 0→1] [NarrationCh1] [ThumbSeq 1→2] [NarrationCh2] ...
//
// Chaque ThumbSeq a une durée de thumbnail_plan.transition_frames.
// Chaque NarrationCh regroupe les segments entre deux chapter starts.
// L'audio est décalé pour commencer au début de la première narration.
//
// Si thumbnail_plan est ABSENT, DeltaMain retombe sur Main (gamma standard).
// ────────────────────────────────────────────────────────────────────────

import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { Background } from "./components/Background";
import { ThumbnailSequence } from "./components/ThumbnailSequence";
import { NarrationChapter } from "./components/NarrationChapter";
import { Main } from "./Main";

export const DeltaMain = ({ timing, roadmap }) => {
  const { durationInFrames } = useVideoConfig();

  // ── Mode gamma standard si pas de thumbnail_plan ──────────────────────
  if (!roadmap.thumbnail_plan || !roadmap.thumbnail_plan.chapters || roadmap.thumbnail_plan.chapters.length === 0) {
    return <Main timing={timing} roadmap={roadmap} />;
  }

  const plan = roadmap.thumbnail_plan;
  const transFrames = plan.transition_frames || 45;
  const chapters = plan.chapters;
  const thumbnailFile = plan.file || "thumbnail.png";

  // ── Construction de la timeline hybride ───────────────────────────────
  let cursor = 0;
  const hybridSeqs = [];

  chapters.forEach((chapter, idx) => {
    // ── Séquence miniature avant ce chapitre ────────────────────────────
    const fromWp = idx === 0 ? null : chapters[idx - 1].waypoint;
    const toWp = chapter.waypoint;

    hybridSeqs.push({
      type: "thumbnail",
      from: cursor,
      duration: transFrames,
      fromWaypoint: fromWp,
      toWaypoint: toWp,
    });
    cursor += transFrames;

    // ── Chapitre narration : segments de start_segment au prochain chapter ──
    const startSeg = chapter.start_segment;
    const endSeg = idx < chapters.length - 1
      ? chapters[idx + 1].start_segment
      : roadmap.timeline.length;

    const chapterSegments = roadmap.timeline.slice(startSeg, endSeg);
    if (chapterSegments.length === 0) return;

    const chapterStartFrame = chapterSegments[0].start_frame;
    const chapterEndFrame = chapterSegments[chapterSegments.length - 1].end_frame;
    const chapterDuration = chapterEndFrame - chapterStartFrame;

    if (chapterDuration <= 0) return;

    hybridSeqs.push({
      type: "narration",
      from: cursor,
      duration: chapterDuration,
      segmentStartIdx: startSeg,
      segmentEndIdx: endSeg,
    });
    cursor += chapterDuration;
  });

  const totalDuration = cursor;
  const audioOffset = transFrames; // Audio commence après la première transition

  return (
    <AbsoluteFill>
      {/* Fond permanent — grain + vignette sur toute la vidéo */}
      <Background style={roadmap.style} />

      {/* Séquences hybrides */}
      {hybridSeqs.map((seq, idx) => {
        if (seq.type === "thumbnail") {
          return (
            <Sequence
              key={`thumb-${idx}`}
              from={seq.from}
              durationInFrames={seq.duration}
              layout="none"
            >
              <ThumbnailSequence
                thumbnailSrc={thumbnailFile}
                fromWaypoint={seq.fromWaypoint}
                toWaypoint={seq.toWaypoint}
                durationInFrames={seq.duration}
              />
            </Sequence>
          );
        }
        // narration
        return (
          <Sequence
            key={`narr-${idx}`}
            from={seq.from}
            durationInFrames={seq.duration}
            layout="none"
          >
            <NarrationChapter
              timing={timing}
              roadmap={roadmap}
              segmentStartIdx={seq.segmentStartIdx}
              segmentEndIdx={seq.segmentEndIdx}
            />
          </Sequence>
        );
      })}

      {/* Piste audio — décalée pour commencer après la première transition miniature */}
      <Sequence from={audioOffset} durationInFrames={Math.max(totalDuration - audioOffset, 1)}>
        <Audio src={staticFile("audio_clean.mp3")} />
      </Sequence>
    </AbsoluteFill>
  );
};
