// src/Root.jsx — F03 SIGISMUND
// Composition principale CRUSADER. Charge dynamiquement timing.json + roadmap.json
// depuis public/ via calculateMetadata (Remotion 4.x).
import React from "react";
import { Composition } from "remotion";
import { Main } from "./Main";
import { BetaMain } from "./BetaMain";

// BYPASS staticFile() — npm install delta en beta corrompt la résolution
// et retourne /public/timing.json au lieu de /timing.json → 404.
// Les fichiers sont dans public/ et servis à la racine par le serveur Remotion.
const fetchData = async () => {
  const [timing, roadmap] = await Promise.all([
    fetch("/timing.json").then((r) => r.json()),
    fetch("/roadmap.json").then((r) => r.json()),
  ]);
  return { timing, roadmap };
};

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
        const { timing, roadmap } = await fetchData();
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
        const { timing, roadmap } = await fetchData();
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
