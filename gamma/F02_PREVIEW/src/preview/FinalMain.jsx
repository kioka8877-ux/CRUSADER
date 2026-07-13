/**
 * FinalMain.jsx — v7 (fix zoom direction + image fixe)
 *
 * Chapitre 1: zoom in vers le waypoint (math corrigée)
 * Chapitres 2+: fragment plein écran, IMAGE FIXE, ne bouge pas
 */
import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "./Background";
import { WorldScene } from "./WorldScene";
import { BetaSubtitle } from "./BetaSubtitle";

export const FinalMain = ({ timing, roadmap, miniaturePlan }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const introDuration = miniaturePlan?.intro_duration ?? 90;
  const zoomLevel = miniaturePlan?.zoom_level ?? 2.5;
  const chapters = miniaturePlan?.chapters || [];
  const timeline = roadmap.timeline;

  // === Trouver le chapitre actif ===
  let activeChapter = null;
  let chapterStartFrame = 0;
  let activeChapterIdx = -1;

  for (let i = 0; i < chapters.length; i++) {
    const ch = chapters[i];
    if (!ch.start_segment) continue;
    const seg = timeline.find(s => s.id === ch.start_segment);
    if (!seg) continue;
    if (frame >= seg.start_frame) {
      activeChapter = ch;
      chapterStartFrame = seg.start_frame;
      activeChapterIdx = i;
    }
  }

  const localFrame = frame - chapterStartFrame;
  const hasIntro = activeChapter && activeChapter.fragment && localFrame < introDuration;

  // === Opacity ===
  const fadeOutFrames = 5;
  let miniOpacity = 0;

  if (hasIntro) {
    if (localFrame < introDuration - fadeOutFrames) {
      miniOpacity = 1;
    } else {
      miniOpacity = interpolate(localFrame, [introDuration - fadeOutFrames, introDuration], [1, 0], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });
    }
  }

  // === Transform ===
  let miniTransform = "scale(1)";

  if (hasIntro) {
    const wps = activeChapter.waypoints || [];
    const isFirst = activeChapterIdx === 0;

    if (isFirst && wps.length >= 1) {
      // === Chapitre 1: zoom in vers le waypoint ===
      // Math corrigée: translate = -(wp - 0.5) * dimension (PAS divisé par scale)
      const wp = wps[0];
      const zoomDuration = Math.floor(introDuration / 2);

      // Position finale: le waypoint doit être au centre de l'écran
      const finalTx = -(wp.x - 0.5) * width;
      const finalTy = -(wp.y - 0.5) * height;

      if (localFrame < zoomDuration) {
        // Phase zoom: scale 1 → zoomLevel, translate 0 → final
        const t = interpolate(localFrame, [0, zoomDuration], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        const scale = interpolate(t, [0, 1], [1, zoomLevel]);
        const tx = interpolate(t, [0, 1], [0, finalTx]);
        const ty = interpolate(t, [0, 1], [0, finalTy]);

        miniTransform = `scale(${scale}) translate(${tx}px, ${ty}px)`;
      } else {
        // Phase statique sur le waypoint
        miniTransform = `scale(${zoomLevel}) translate(${finalTx}px, ${finalTy}px)`;
      }
    }
    // Chapitres 2+: PAS de transform, l'image reste fixe plein écran
    // miniTransform reste "scale(1)" — le fragment remplit l'écran via objectFit: cover
  }

  return (
    <AbsoluteFill>
      {/* === Contenu normal — TOUJOURS rendu === */}
      <Background style={roadmap.style} />
      <WorldScene timeline={roadmap.timeline} style={roadmap.style} />
      <BetaSubtitle timeline={roadmap.timeline} style={roadmap.style} timing={timing} />

      {/* === Overlay fragment === */}
      {miniOpacity > 0 && activeChapter?.fragment && (
        <AbsoluteFill
          style={{
            opacity: miniOpacity,
            overflow: "hidden",
            backgroundColor: "#000",
            zIndex: 100,
          }}
        >
          <AbsoluteFill
            style={{
              transform: miniTransform,
              transformOrigin: "center center",
            }}
          >
            <Img
              src={activeChapter.fragment}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
