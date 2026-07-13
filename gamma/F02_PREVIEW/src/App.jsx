import React, { useState, useMemo, useCallback } from "react";
import { Player } from "@remotion/player";
import { BetaMain } from "./preview/BetaMain";
import { FinalMain } from "./preview/FinalMain";
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
    thumbnailURL: null,
    transition_frames: 45,
    intro_duration: 60,    // 2s à 30fps
    zoom_level: 2.5,       // degré de zoom
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
  const finalProps = { timing: defaultTiming, roadmap, miniaturePlan };

  const handleChange = (key, value) => {
    setStyleOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const handleMiniatureChange = useCallback((plan) => {
    setMiniaturePlan((prev) => ({
      ...prev,
      ...plan,
      // Conserver thumbnailURL, intro_duration, zoom_level si pas dans plan
      thumbnailURL: plan.thumbnailURL ?? prev.thumbnailURL,
      intro_duration: plan.intro_duration ?? prev.intro_duration,
      zoom_level: plan.zoom_level ?? prev.zoom_level,
    }));
  }, []);

  const handleIntroDuration = (val) => {
    setMiniaturePlan((prev) => ({ ...prev, intro_duration: val }));
  };

  const handleZoomLevel = (val) => {
    setMiniaturePlan((prev) => ({ ...prev, zoom_level: val }));
  };

  const handleThumbnailUpload = (dataURL, filename) => {
    setMiniaturePlan((prev) => ({
      ...prev,
      file: filename,
      thumbnailURL: dataURL,
    }));
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
            <button
              onClick={() => setActiveTab("final")}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                activeTab === "final"
                  ? "bg-amber-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              🎬 Video Finale
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
          onThumbnailUpload={handleThumbnailUpload}
          introDuration={miniaturePlan.intro_duration}
          zoomLevel={miniaturePlan.zoom_level}
          onIntroDurationChange={handleIntroDuration}
          onZoomLevelChange={handleZoomLevel}
        />
      )}

      {activeTab === "final" && (
        <div className="flex flex-1 overflow-hidden">
          {/* Control panel — sliders pour Video Finale */}
          <aside className="w-80 border-r border-gray-800 overflow-y-auto p-4">
            <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
              🎬 Intro Miniature
            </h3>

            <div className="mb-3">
              <label className="text-xs text-gray-400 flex justify-between">
                <span>Durée intro</span>
                <span className="font-mono text-amber-400">
                  {(miniaturePlan.intro_duration / fps).toFixed(1)}s ({miniaturePlan.intro_duration}f)
                </span>
              </label>
              <input
                type="range"
                min="30"
                max="150"
                step="15"
                value={miniaturePlan.intro_duration}
                onChange={(e) => handleIntroDuration(parseInt(e.target.value))}
                className="w-full mt-1 accent-amber-500"
              />
            </div>

            <div className="mb-3">
              <label className="text-xs text-gray-400 flex justify-between">
                <span>Degré zoom</span>
                <span className="font-mono text-amber-400">{miniaturePlan.zoom_level}×</span>
              </label>
              <input
                type="range"
                min="1.5"
                max="5"
                step="0.5"
                value={miniaturePlan.zoom_level}
                onChange={(e) => handleZoomLevel(parseFloat(e.target.value))}
                className="w-full mt-1 accent-amber-500"
              />
            </div>

            <div className="mt-6 p-3 bg-gray-900 rounded text-xs text-gray-500 leading-relaxed">
              <p className="mb-2"><b className="text-gray-400">Flux par chapitre :</b></p>
              <p>1. Miniature plein écran (silence)</p>
              <p>2. Zoom IN vers waypoint 1</p>
              <p>3. Pan latéral entre waypoints</p>
              <p>4. Coupe → contenu normal + audio</p>
            </div>

            {!miniaturePlan.thumbnailURL && (
              <div className="mt-4 p-3 bg-red-950/50 border border-red-800 rounded text-xs text-red-400">
                ⚠️ Uploade une miniature dans l'onglet Miniature d'abord.
              </div>
            )}

            {miniaturePlan.chapters.filter(c => c.waypoint).length < 2 && (
              <div className="mt-4 p-3 bg-yellow-950/50 border border-yellow-800 rounded text-xs text-yellow-400">
                ⚠️ Place au moins 2 waypoints dans l'onglet Miniature.
              </div>
            )}
          </aside>

          {/* Player Video Finale */}
          <main className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
            <DeviceFrame label="Desktop — 1920×1080" aspect="16/9">
              <Player
                component={FinalMain}
                inputProps={finalProps}
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
                component={FinalMain}
                inputProps={finalProps}
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
    </div>
  );
}
