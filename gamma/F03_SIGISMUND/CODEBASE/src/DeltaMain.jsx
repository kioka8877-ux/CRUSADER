/**
 * DeltaMain.jsx — F03 SIGISMUND (v4 — announce-sync instant)
 *
 * FIXES v4:
 * - Miniature instantanée: opacity=1 dès le frame 1 (plus de fadeIn)
 * - Gap frames 0-19: premier chapitre démarre à frame 0 pour couvrir le vide
 * - Fade out gardé uniquement à la fin de l'annonce
 *
 * Source de vérité: announce_start_frame → announce_end_frame
 * - Contenu normal (BetaMain: capsules + sous-titres + audio) TOUJOURS rendu
 * - Miniature overlay PENDANT l'annonce du nom
 * - Ch.1: zoom vers le rectangle cible (crop)
 * - Ch.2+: pan caméra sur l'image complète de wp1 → wp2
 *
 * Fallback: si pas d'announce frames → utilise start_segment + intro_duration (legacy)
 * Si roadmap.miniature absent → fallback sur Main (gamma standard).
 */
import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { Background } from "./components/Background";
import { WorldScene } from "./components/WorldScene";
import { BetaSubtitle } from "./components/BetaSubtitle";
import { Main } from "./Main";

export const DeltaMain = ({ timing, roadmap }) => {
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
        // ANNOUNCE-SYNC: use announce_start/end_frame if present
        let startFrame = null;
        let endFrame = null;

        if (chapter.announce_start_frame != null && chapter.announce_end_frame != null) {
          startFrame = chapter.announce_start_frame;
          endFrame = chapter.announce_end_frame;
        } else if (chapter.start_segment) {
          // LEGACY fallback
          const seg = timeline.find(s => s.id === chapter.start_segment);
          if (seg) {
            startFrame = seg.start_frame;
            endFrame = seg.start_frame + introDuration;
          }
        }

        if (startFrame == null) return null;

        // FIX: premier chapitre démarre à frame 0 pour couvrir le gap
        if (idx === 0 && startFrame > 0) {
          endFrame = endFrame + startFrame; //延长 end par le gap
          startFrame = 0;
        }

        return (
          <MiniatureOverlay
            key={idx}
            chapter={chapter}
            chapterIdx={idx}
            announceStart={startFrame}
            announceEnd={endFrame}
          />
        );
      })}

      {/* === Audio === */}
      <Audio src={staticFile("audio_clean.mp3")} />
    </AbsoluteFill>
  );
};

/**
 * MiniatureOverlay — affiche la miniature pendant la fenêtre d'annonce.
 * FIX v4: opacity instantanée (plus de fadeIn), fade out seulement à la fin.
 */
const MiniatureOverlay = ({ chapter, chapterIdx, announceStart, announceEnd }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const localFrame = frame - announceStart;
  const announceDuration = announceEnd - announceStart;
  const hasIntro = (chapter.imageURL || chapter.fragment) && localFrame >= 0 && localFrame < announceDuration;

  if (!hasIntro) return null;

  // === Opacity — INSTANTANÉ, fade out seulement ===
  const fadeOutFrames = 5;
  let miniOpacity = 1; // FIX: opacity=1 immédiatement, plus de fadeIn

  if (localFrame >= announceDuration - fadeOutFrames) {
    miniOpacity = interpolate(localFrame, [announceDuration - fadeOutFrames, announceDuration], [1, 0], {
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

    const zoomDuration = Math.floor(announceDuration / 2);

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

    const wp1Full = {
      x: crop.x1 + wps[0].x * (crop.x2 - crop.x1),
      y: crop.y1 + wps[0].y * (crop.y2 - crop.y1),
    };
    const wp2Full = {
      x: crop.x1 + wps[1].x * (crop.x2 - crop.x1),
      y: crop.y1 + wps[1].y * (crop.y2 - crop.y1),
    };

    const maxOffsetX = Math.max(Math.abs(wp1Full.x - 0.5), Math.abs(wp2Full.x - 0.5));
    const maxOffsetY = Math.max(Math.abs(wp1Full.y - 0.5), Math.abs(wp2Full.y - 0.5));
    const maxOffset = Math.max(maxOffsetX, maxOffsetY);

    const minScale = maxOffset < 0.45 ? 1 / (1 - 2 * maxOffset) : 10;
    const panScale = Math.min(minScale * 1.15, 8);

    const tx1 = -panScale * (wp1Full.x - 0.5) * width;
    const ty1 = -panScale * (wp1Full.y - 0.5) * height;
    const tx2 = -panScale * (wp2Full.x - 0.5) * width;
    const ty2 = -panScale * (wp2Full.y - 0.5) * height;

    const panDuration = Math.floor(announceDuration * 0.7);

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
