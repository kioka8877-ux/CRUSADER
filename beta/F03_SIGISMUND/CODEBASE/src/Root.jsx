// src/Root.jsx — F03 SIGISMUND
// Composition principale CRUSADER. timing.json + roadmap.json sont importés
// directement comme modules statiques (bundle-time) pour éviter le 404 réseau
// observé quand Puppeteer essaie de fetch /timing.json dans le runner CI.
import React from "react";
import { Composition } from "remotion";
import { Main } from "./Main";
import { BetaMain } from "./BetaMain";

// Import statique des JSON depuis public/ — résolu par esbuild au bundle time.
// Zéro fetch réseau, zéro 404 possible.
import timing from "../public/timing.json";
import roadmap from "../public/roadmap.json";

const fetchData = () => ({ timing, roadmap });

export const Root = () => {
  return (
    <>
    <Composition
      id="CrusaderShort"
      component={Main}
      // Placeholders — écrasés par calculateMetadata
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
      calculateMetadata={async () => {
        const { timing, roadmap } = fetchData();
        return {
          durationInFrames: timing.meta.total_frames,
          fps: timing.meta.fps,
          width: roadmap.meta.width,
          height: roadmap.meta.height,
          props: { timing, roadmap },
        };
      }}
    />

    <Composition
      id="CrusaderBeta"
      component={BetaMain}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      calculateMetadata={async () => {
        const { timing, roadmap } = fetchData();
        return {
          durationInFrames: timing.meta.total_frames,
          fps: timing.meta.fps,
          width: roadmap.meta.width,
          height: roadmap.meta.height,
          props: { timing, roadmap },
        };
      }}
    />
    </>
  );
};
