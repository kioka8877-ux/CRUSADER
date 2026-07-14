/**
 * FinalMain.jsx — v10 (announce-sync)
 *
 * BREAKING CHANGE: la miniature apparaît PENDANT l'annonce du nom du chapitre,
 * pas pendant un silence/intro_duration fixe.
 *
 * Source de vérité: announce_start_frame → announce_end_frame
 * - Ch.1: zoom vers le rectangle cible (crop)
 * - Ch.2+: pan caméra sur l'image complète de wp1 → wp2
 * - Fade out à la fin de l'annonce
 *
 * Fallback: si pas d'announce frames → utilise start_segment + intro_duration (legacy)
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
  const chapters = miniaturePlan?.chapters || [];
  const timeline = roadmap.timeline;

  // === Trouver le chapitre actif ===
  let activeChapter = null;
  let activeChapterIdx = -1;
  let announceStart = 0;
  let announceEnd = 0;

  for (let i = 0; i < chapters.length; i++) {
    const ch = chapters[i];
    
    // ANNOUNCE-SYNC: use announce_start/end_frame if present
    if (ch.announce_start_frame != null && ch.announce_end_frame != null) {
      if (frame >= ch.announce_start_frame && frame < ch.announce_end_frame) {
        activeChapter = ch;
        activeChapterIdx = i;
        announceStart = ch.announce_start_frame;
        announceEnd = ch.announce_end_frame;
      }
    } else {
      // LEGACY fallback: start_segment + intro_duration
      if (!ch.start_segment) continue;
      const seg = timeline.find(s => s.id === ch.start_segment);
      if (!seg) continue;
      if (frame >= seg.start_frame && frame < seg.start_frame + introDuration) {
        activeChapter = ch;
        activeChapterIdx = i;
        announceStart = seg.start_frame;
        announceEnd = seg.start_frame + introDuration;
      }
    }
  }

  const localFrame = frame - announceStart;
  const announceDuration = announceEnd - announceStart;
  const hasIntro = activeChapter && (activeChapter.imageURL || activeChapter.fragment) && localFrame >= 0 && localFrame < announceDuration;

  // === Opacity ===
  const fadeInFrames = 3;
  const fadeOutFrames = 5;
  let miniOpacity = 0;

  if (hasIntro) {
    if (localFrame < fadeInFrames) {
      miniOpacity = interpolate(localFrame, [0, fadeInFrames], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });
    } else if (localFrame < announceDuration - fadeOutFrames) {
      miniOpacity = 1;
    } else {
      miniOpacity = interpolate(localFrame, [announceDuration - fadeOutFrames, announceDuration], [1, 0], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });
    }
  }

  // === Transform ===
  let miniTransform = "translate(0px, 0px) scale(1)";
  let imgSrc = null;

  if (hasIntro) {
    const isFirst = activeChapterIdx === 0;
    imgSrc = activeChapter.imageURL || activeChapter.fragment;

    if (isFirst && activeChapter.crop) {
      // === Chapitre 1: zoom vers le rectangle cible ===
      const crop = activeChapter.crop;
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
    } else if (!isFirst && activeChapter.crop && activeChapter.waypoints?.length >= 2) {
      // === Chapitres 2+: pan caméra sur l'image COMPLETE ===
      const crop = activeChapter.crop;
      const wps = activeChapter.waypoints;

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
  }

  return (
    <AbsoluteFill>
      <Background style={roadmap.style} />
      <WorldScene timeline={roadmap.timeline} style={roadmap.style} />
      <BetaSubtitle timeline={roadmap.timeline} style={roadmap.style} timing={timing} />

      {miniOpacity > 0 && imgSrc && (
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
              src={imgSrc}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
