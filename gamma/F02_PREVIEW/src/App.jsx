import React, { useState, useMemo } from "react";
import { Player } from "@remotion/player";
import { BetaMain } from "./preview/BetaMain";
import { ControlPanel } from "./ControlPanel";
import { DeviceFrame } from "./DeviceFrame";
import "./index.css";

// ── Données par défaut (remplacer par vos propres fichiers) ──
import defaultRoadmap from "../public/roadmap.json";
import defaultTiming from "../public/timing.json";

export default function App() {
  /* ── State : style éditable en live ── */
  const [styleOverrides, setStyleOverrides] = useState({});

  const roadmap = useMemo(() => ({
    ...defaultRoadmap,
    style: { ...defaultRoadmap.style, ...styleOverrides },
  }), [styleOverrides]);

  const meta = roadmap.meta;
  const fps = meta.fps || 30;
  const totalFrames = defaultTiming.meta?.total_frames || 531;

  const inputProps = { timing: defaultTiming, roadmap };

  const handleChange = (key, value) => {
    setStyleOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const handleExport = () => {
    const blob = new Blob(
      [JSON.stringify(roadmap, null, 2)],
      { type: "application/json" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "roadmap.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* ── Header ── */}
      <header className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
        <h1 className="text-xl font-bold tracking-wide">
          🎬 F02 — CRUSADER Preview
        </h1>
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded font-semibold text-sm"
        >
          📥 Export roadmap.json
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Panneau contrôles ── */}
        <aside className="w-80 border-r border-gray-800 overflow-y-auto p-4">
          <ControlPanel
            style={roadmap.style}
            onChange={handleChange}
          />
        </aside>

        {/* ── Previews ── */}
        <main className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
          {/* Desktop (16:9) */}
          <DeviceFrame label="Desktop — 1920×1080" aspect="16/9">
            <Player
              component={BetaMain}
              inputProps={inputProps}
              durationInFrames={totalFrames}
              fps={fps}
              compositionWidth={meta.width || 1920}
              compositionHeight={meta.height || 1080}
              style={{ width: "100%" }}
              controls
              loop
            />
          </DeviceFrame>

          {/* iPhone 16 Pro Max (19.5:9 → 9:19.5) */}
          <DeviceFrame label="iPhone 16 Pro Max — 1320×2868" aspect="9/19.5">
            <Player
              component={BetaMain}
              inputProps={inputProps}
              durationInFrames={totalFrames}
              fps={fps}
              compositionWidth={meta.width || 1920}
              compositionHeight={meta.height || 1080}
              style={{ width: "100%" }}
              controls
              loop
            />
          </DeviceFrame>
        </main>
      </div>
    </div>
  );
}
