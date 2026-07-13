import React, { useState, useMemo, useCallback } from "react";
import { Player } from "@remotion/player";
import { BetaMain } from "./preview/BetaMain";
import { ControlPanel } from "./ControlPanel";
import { DeviceFrame } from "./DeviceFrame";
import { MiniatureEditor } from "./MiniatureEditor";
import "./index.css";

// ── Données par défaut ──
import defaultRoadmap from "../public/roadmap.json";
import defaultTiming from "../public/timing.json";

export default function App() {
  /* ── Onglet actif ── */
  const [activeTab, setActiveTab] = useState("preview");

  /* ── State : style éditable en live ── */
  const [styleOverrides, setStyleOverrides] = useState({});

  /* ── State : miniature plan ── */
  const [miniaturePlan, setMiniaturePlan] = useState({
    file: null,
    transition_frames: 45,
    chapters: [],
  });

  const roadmap = useMemo(() => ({
    ...defaultRoadmap,
    style: { ...defaultRoadmap.style, ...styleOverrides },
    miniature: miniaturePlan,
  }), [styleOverrides, miniaturePlan]);

  const meta = roadmap.meta;
  const fps = meta.fps || 30;
  const totalFrames = defaultTiming.meta?.total_frames || 531;

  const inputProps = { timing: defaultTiming, roadmap };

  const handleChange = (key, value) => {
    setStyleOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const handleMiniatureChange = useCallback((plan) => {
    setMiniaturePlan(plan);
  }, []);

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
      {/* Header */}
      <header className="px-6 py-3 border-b border-gray-800 flex items-center justify-between">
        <h1 className="text-xl font-bold tracking-wide">
          🎬 F02 — CRUSADER Preview
        </h1>
        <div className="flex items-center gap-4">
          {/* Tab switcher */}
          <div className="flex gap-1 bg-gray-900 rounded-lg p-1">
            <button
              onClick={() => setActiveTab("preview")}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                activeTab === "preview"
                  ? "bg-amber-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              🎥 Preview
            </button>
            <button
              onClick={() => setActiveTab("miniature")}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                activeTab === "miniature"
                  ? "bg-amber-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              🗺️ Miniature
            </button>
          </div>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded font-semibold text-sm"
          >
            📥 Export roadmap.json
          </button>
        </div>
      </header>

      {/* Tab content */}
      {activeTab === "preview" && (
        <div className="flex flex-1 overflow-hidden">
          {/* Control panel */}
          <aside className="w-80 border-r border-gray-800 overflow-y-auto p-4">
            <ControlPanel
              style={roadmap.style}
              onChange={handleChange}
            />
          </aside>

          {/* Previews */}
          <main className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
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
      )}

      {activeTab === "miniature" && (
        <MiniatureEditor
          timeline={defaultRoadmap.timeline}
          onMiniatureChange={handleMiniatureChange}
        />
      )}
    </div>
  );
}
