// src/Root.jsx — F03 SIGISMUND
// Composition principale CRUSADER. Charge dynamiquement timing.json + roadmap.json
// depuis public/ via calculateMetadata (Remotion 4.x).
import React from "react";
import { Composition, staticFile } from "remotion";
import { Main } from "./Main";
import { BetaMain } from "./BetaMain";

const fetchData = async () => {
  const [timing, roadmap] = await Promise.all([
    fetch(staticFile("timing.json")).then((r) => r.json()),
    fetch(staticFile("roadmap.json")).then((r) => r.json()),
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
