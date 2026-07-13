/**
 * FinalMain.jsx — v9 (image complète + math correcte)
 *
 * Chapitre 1: zoom vers le rectangle cible
 *   - Image complète + crop comme cible
 *   - transform: translate() scale() — ordre correct
 *   - finalScale = 1 / min(cropW, cropH) → le rectangle remplit l'écran
 *
 * Chapitres 2+: caméra pan sur l'image COMPLETE (pas le fragment coupé)
 *   - L'image COMPLETE remplit l'écran (objectFit: cover)
 *   - Scale auto calculé pour couvrir l'écran pendant tout le pan
 *   - Pan de wp1 → wp2 (coordonnées converties crop → image complète)
 *   - PAS de bord noir — l'image est toujours plus grande que l'écran
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
  const hasIntro = activeChapter && (activeChapter.fragment || activeChapter.imageURL) && localFrame < introDuration;

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
  let miniTransform = "translate(0px, 0px) scale(1)";
  let imgSrc = null;

  if (hasIntro) {
    const isFirst = activeChapterIdx === 0;

    // Image source: l'image COMPLETE pour tous les chapitres
    imgSrc = activeChapter.imageURL || activeChapter.fragment;

    if (isFirst && activeChapter.crop) {
      // === Chapitre 1: zoom vers le rectangle cible ===
      const crop = activeChapter.crop;
      const cropW = crop.x2 - crop.x1;
      const cropH = crop.y2 - crop.y1;
      const cropCenterX = crop.x1 + cropW / 2;
      const cropCenterY = crop.y1 + cropH / 2;

      // Scale final: la zone cible remplit l'écran
      const finalScale = 1 / Math.min(cropW, cropH);

      // Translate final: centrer le centre du rectangle sur l'écran
      // Avec transform: translate() scale(), le scale est appliqué d'abord,
      // puis le translate. Donc tx = -S * (center - 0.5) * dimension
      const finalTx = -finalScale * (cropCenterX - 0.5) * width;
      const finalTy = -finalScale * (cropCenterY - 0.5) * height;

      const zoomDuration = Math.floor(introDuration / 2);

      if (localFrame < zoomDuration) {
        // Phase zoom: scale 1 → finalScale, translate 0 → final
        const t = interpolate(localFrame, [0, zoomDuration], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        const easedT = t * t * (3 - 2 * t); // smoothstep

        const scale = interpolate(easedT, [0, 1], [1, finalScale]);
        const tx = interpolate(easedT, [0, 1], [0, finalTx]);
        const ty = interpolate(easedT, [0, 1], [0, finalTy]);

        miniTransform = `translate(${tx}px, ${ty}px) scale(${scale})`;
      } else {
        // Phase statique sur la cible
        miniTransform = `translate(${finalTx}px, ${finalTy}px) scale(${finalScale})`;
      }
    } else if (!isFirst && activeChapter.crop && activeChapter.waypoints?.length >= 2) {
      // === Chapitres 2+: pan caméra sur l'image COMPLETE ===
      const crop = activeChapter.crop;
      const wps = activeChapter.waypoints;

      // Convertir waypoints de coordonnées crop (0-1 dans le crop)
      // vers coordonnées image complète (0-1 sur l'image entière)
      const wp1Full = {
        x: crop.x1 + wps[0].x * (crop.x2 - crop.x1),
        y: crop.y1 + wps[0].y * (crop.y2 - crop.y1),
      };
      const wp2Full = {
        x: crop.x1 + wps[1].x * (crop.x2 - crop.x1),
        y: crop.y1 + wps[1].y * (crop.y2 - crop.y1),
      };

      // === Calculer le scale pour couvrir l'écran pendant tout le pan ===
      // Avec transform: translate() scale(S):
      //   - L'image est scaled par S autour du centre
      //   - Puis translatée par (tx, ty)
      //   - Pour couvrir l'écran: |tx| <= (S-1) * width / 2
      //   - tx = -S * (wp - 0.5) * width
      //   - Donc: S * |wp - 0.5| <= (S-1) / 2
      //   - Soit: S >= 1 / (1 - 2 * |wp - 0.5|)
      const maxOffsetX = Math.max(
        Math.abs(wp1Full.x - 0.5),
        Math.abs(wp2Full.x - 0.5)
      );
      const maxOffsetY = Math.max(
        Math.abs(wp1Full.y - 0.5),
        Math.abs(wp2Full.y - 0.5)
      );
      const maxOffset = Math.max(maxOffsetX, maxOffsetY);

      // Scale minimum pour couvrir, avec 15% de marge
      const minScale = maxOffset < 0.45 ? 1 / (1 - 2 * maxOffset) : 10;
      const panScale = Math.min(minScale * 1.15, 8); // 15% marge, max 8x

      // Translate pour centrer wp1 au début, wp2 à la fin
      const tx1 = -panScale * (wp1Full.x - 0.5) * width;
      const ty1 = -panScale * (wp1Full.y - 0.5) * height;
      const tx2 = -panScale * (wp2Full.x - 0.5) * width;
      const ty2 = -panScale * (wp2Full.y - 0.5) * height;

      // Le pan prend 70% de l'intro, puis on reste sur wp2
      const panDuration = Math.floor(introDuration * 0.7);

      if (localFrame < panDuration) {
        const t = interpolate(localFrame, [0, panDuration], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        const easedT = t * t * (3 - 2 * t); // smoothstep

        const tx = interpolate(easedT, [0, 1], [tx1, tx2]);
        const ty = interpolate(easedT, [0, 1], [ty1, ty2]);

        miniTransform = `translate(${tx}px, ${ty}px) scale(${panScale})`;
      } else {
        miniTransform = `translate(${tx2}px, ${ty2}px) scale(${panScale})`;
      }
    } else {
      // Pas de crop/waypoints: image fixe plein écran
      miniTransform = "translate(0px, 0px) scale(1)";
    }
  }

  return (
    <AbsoluteFill>
      {/* === Contenu normal — TOUJOURS rendu === */}
      <Background style={roadmap.style} />
      <WorldScene timeline={roadmap.timeline} style={roadmap.style} />
      <BetaSubtitle timeline={roadmap.timeline} style={roadmap.style} timing={timing} />

      {/* === Overlay image miniature === */}
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
