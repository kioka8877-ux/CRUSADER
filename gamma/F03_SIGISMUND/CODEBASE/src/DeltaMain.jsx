/**
 * DeltaMain.jsx — F03 SIGISMUND (v2 — overlay approach)
 *
 * Au lieu d'une timeline séquentielle [Thumb][Narr][Thumb][Narr],
 * on utilise une approche OVERLAY :
 * - Le contenu normal (BetaMain: capsules + sous-titres + audio) est TOUJOURS rendu
 * - La miniature est superposée pendant intro_duration frames au début de chaque chapitre
 * - Ch.1: zoom vers le rectangle cible (crop)
 * - Ch.2+: pan caméra sur l'image complète de wp1 → wp2
 *
 * Si roadmap.miniature est absent → fallback sur Main (gamma standard).
 */
import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { Background } from "./components/Background";
import { WorldScene } from "./components/WorldScene";
import { BetaSubtitle } from "./components/BetaSubtitle";
import { Main } from "./Main";

export const DeltaMain = ({ timing, roadmap }) => {
  const { durationInFrames } = useVideoConfig();

  // Fallback si pas de miniature
  if (!roadmap.miniature || !roadmap.miniature.chapters || roadmap.miniature.chapters.length === 0) {
    return <Main timing={timing} roadmap={roadmap} />;
  }

  const plan = roadmap.miniature;
  const introDuration = plan.intro_duration ?? 90;
  const chapters = plan.chapters;
  const timeline = roadmap.timeline;

  return (
    <AbsoluteFill>
      {/* === Contenu normal — TOUJOURS rendu === */}
      <Background style={roadmap.style} />
      <WorldScene timeline={timeline} style={roadmap.style} />
      <BetaSubtitle timeline={timeline} style={roadmap.style} timing={timing} />

      {/* === Overlays miniatures par chapitre === */}
      {chapters.map((chapter, idx) => {
        if (!chapter.start_segment) return null;
        const seg = timeline.find(s => s.id === chapter.start_segment);
        if (!seg) return null;

        return (
          <MiniatureOverlay
            key={idx}
            chapter={chapter}
            chapterIdx={idx}
            chapterStartFrame={seg.start_frame}
            introDuration={introDuration}
          />
        );
      })}

      {/* === Audio === */}
      <Audio src={staticFile("audio_clean.mp3")} />
    </AbsoluteFill>
  );
};

/**
 * MiniatureOverlay — affiche la miniature par-dessus le contenu pendant intro_duration frames.
 * Ch.1: zoom vers rectangle cible (crop)
 * Ch.2+: pan caméra sur image complète de wp1 → wp2
 */
const MiniatureOverlay = ({ chapter, chapterIdx, chapterStartFrame, introDuration }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const localFrame = frame - chapterStartFrame;
  const hasIntro = (chapter.imageURL || chapter.fragment) && localFrame >= 0 && localFrame < introDuration;

  if (!hasIntro) return null;

  // === Opacity ===
  const fadeOutFrames = 5;
  let miniOpacity = 0;

  if (localFrame < introDuration - fadeOutFrames) {
    miniOpacity = 1;
  } else {
    miniOpacity = interpolate(localFrame, [introDuration - fadeOutFrames, introDuration], [1, 0], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });
  }

  // === Transform ===
  let miniTransform = "translate(0px, 0px) scale(1)";
  let imgSrc = chapter.imageURL || chapter.fragment;
  const isFirst = chapterIdx === 0;

  if (isFirst && chapter.crop) {
    // === Chapitre 1: zoom vers le rectangle cible ===
    const crop = chapter.crop;
    const cropW = crop.x2 - crop.x1;
    const cropH = crop.y2 - crop.y1;
    const cropCenterX = crop.x1 + cropW / 2;
    const cropCenterY = crop.y1 + cropH / 2;

    const finalScale = 1 / Math.min(cropW, cropH);
    const finalTx = -finalScale * (cropCenterX - 0.5) * width;
    const finalTy = -finalScale * (cropCenterY - 0.5) * height;

    const zoomDuration = Math.floor(introDuration / 2);

    if (localFrame < zoomDuration) {
      const t = interpolate(localFrame, [0, zoomDuration], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });
      const easedT = t * t * (3 - 2 * t);

      const scale = interpolate(easedT, [0, 1], [1, finalScale]);
      const tx = interpolate(easedT, [0, 1], [0, finalTx]);
      const ty = interpolate(easedT, [0, 1], [0, finalTy]);

      miniTransform = `translate(${tx}px, ${ty}px) scale(${scale})`;
    } else {
      miniTransform = `translate(${finalTx}px, ${finalTy}px) scale(${finalScale})`;
    }
  } else if (!isFirst && chapter.crop && chapter.waypoints?.length >= 2) {
    // === Chapitres 2+: pan caméra sur l'image COMPLETE ===
    const crop = chapter.crop;
    const wps = chapter.waypoints;

    // Convertir waypoints de coordonnées crop → image complète
    const wp1Full = {
      x: crop.x1 + wps[0].x * (crop.x2 - crop.x1),
      y: crop.y1 + wps[0].y * (crop.y2 - crop.y1),
    };
    const wp2Full = {
      x: crop.x1 + wps[1].x * (crop.x2 - crop.x1),
      y: crop.y1 + wps[1].y * (crop.y2 - crop.y1),
    };

    // Scale auto pour couvrir l'écran pendant tout le pan
    const maxOffsetX = Math.max(Math.abs(wp1Full.x - 0.5), Math.abs(wp2Full.x - 0.5));
    const maxOffsetY = Math.max(Math.abs(wp1Full.y - 0.5), Math.abs(wp2Full.y - 0.5));
    const maxOffset = Math.max(maxOffsetX, maxOffsetY);

    const minScale = maxOffset < 0.45 ? 1 / (1 - 2 * maxOffset) : 10;
    const panScale = Math.min(minScale * 1.15, 8);

    const tx1 = -panScale * (wp1Full.x - 0.5) * width;
    const ty1 = -panScale * (wp1Full.y - 0.5) * height;
    const tx2 = -panScale * (wp2Full.x - 0.5) * width;
    const ty2 = -panScale * (wp2Full.y - 0.5) * height;

    const panDuration = Math.floor(introDuration * 0.7);

    if (localFrame < panDuration) {
      const t = interpolate(localFrame, [0, panDuration], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });
      const easedT = t * t * (3 - 2 * t);

      const tx = interpolate(easedT, [0, 1], [tx1, tx2]);
      const ty = interpolate(easedT, [0, 1], [ty1, ty2]);

      miniTransform = `translate(${tx}px, ${ty}px) scale(${panScale})`;
    } else {
      miniTransform = `translate(${tx2}px, ${ty2}px) scale(${panScale})`;
    }
  }

  if (miniOpacity <= 0) return null;

  return (
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
        <img
          src={imgSrc}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
