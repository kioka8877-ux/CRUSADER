import React, { useState, useRef, useCallback, useEffect } from "react";

/**
 * MiniatureEditor — Port React de l'onglet MINIATURE du viewer F02
 *
 * Fonctions :
 * - Upload PNG miniature (drag & drop ou clic)
 * - Ajout/suppression de chapitres
 * - Clic sur la miniature pour placer des waypoints caméra
 * - Slider durée de transition
 * - Simulation du mouvement caméra entre waypoints
 * - Export des données dans roadmap.json
 */
export const MiniatureEditor = ({ timeline, onMiniatureChange }) => {
  const [thumbnailURL, setThumbnailURL] = useState(null);
  const [thumbnailName, setThumbnailName] = useState("");
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState(-1);
  const [transFrames, setTransFrames] = useState(45);
  const [simulating, setSimulating] = useState(false);
  const fileInputRef = useRef(null);
  const canvasWrapRef = useRef(null);
  const animRef = useRef(null);

  /* ── Upload miniature ── */
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setThumbnailName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => {
      setThumbnailURL(ev.target.result);
      if (chapters.length === 0) {
        addChapter();
      }
    };
    reader.readAsDataURL(file);
  };

  /* ── Chapitres ── */
  const addChapter = () => {
    const defaultSeg = timeline.length > 0 ? timeline[0].id : 1;
    const newChapter = {
      id: Date.now(),
      label: `Chapitre ${chapters.length + 1}`,
      start_segment: defaultSeg,
      waypoint: null,
    };
    setChapters((prev) => [...prev, newChapter]);
    setSelectedChapter(chapters.length);
  };

  const removeChapter = (idx) => {
    setChapters((prev) => prev.filter((_, i) => i !== idx));
    setSelectedChapter(-1);
  };

  const updateChapterLabel = (idx, label) => {
    setChapters((prev) =>
      prev.map((c, i) => (i === idx ? { ...c, label } : c))
    );
  };

  const updateChapterSegment = (idx, segId) => {
    setChapters((prev) =>
      prev.map((c, i) => (i === idx ? { ...c, start_segment: parseInt(segId) } : c))
    );
  };

  /* ── Clic sur miniature → place waypoint ── */
  const handleCanvasClick = (e) => {
    if (e.target.classList.contains("mini-dot") || e.target.closest(".mini-dot")) return;
    if (selectedChapter < 0 || !thumbnailURL) return;

    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    setChapters((prev) =>
      prev.map((c, i) =>
        i === selectedChapter
          ? { ...c, waypoint: { x: parseFloat(x.toFixed(4)), y: parseFloat(y.toFixed(4)) } }
          : c
      )
    );
  };

  /* ── Simulation mouvement caméra ── */
  const simulateCamera = () => {
    const wpChapters = chapters.filter((c) => c.waypoint);
    if (wpChapters.length < 2) return;
    setSimulating(true);
  };

  useEffect(() => {
    if (!simulating) return;

    const wpChapters = chapters.filter((c) => c.waypoint);
    if (wpChapters.length < 2) {
      setSimulating(false);
      return;
    }

    const wrap = canvasWrapRef.current;
    if (!wrap) {
      setSimulating(false);
      return;
    }

    let startTime = null;
    const duration = 3000; // 3s

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Clear previous cam dots/lines
      wrap.querySelectorAll(".mini-cam-dot, .mini-cam-line").forEach((el) => el.remove());

      if (progress >= 1) {
        setSimulating(false);
        return;
      }

      const totalProgress = progress * (wpChapters.length - 1);
      const segIdx = Math.floor(totalProgress);
      const segProgress = totalProgress - segIdx;

      if (segIdx >= wpChapters.length - 1) {
        setSimulating(false);
        return;
      }

      const from = wpChapters[segIdx].waypoint;
      const to = wpChapters[segIdx + 1].waypoint;
      const x = from.x + (to.x - from.x) * segProgress;
      const y = from.y + (to.y - from.y) * segProgress;

      // Draw line
      const line = document.createElement("div");
      line.className = "mini-cam-line";
      const dx = (to.x - from.x) * 100;
      const dy = (to.y - from.y) * 100;
      const len = Math.sqrt(dx * dx + dy * dy);
      const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
      line.style.left = `${from.x * 100}%`;
      line.style.top = `${from.y * 100}%`;
      line.style.width = `${len}%`;
      line.style.transform = `rotate(${angle}deg)`;
      wrap.appendChild(line);

      // Draw cam dot
      const camDot = document.createElement("div");
      camDot.className = "mini-cam-dot";
      camDot.style.left = `${x * 100}%`;
      camDot.style.top = `${y * 100}%`;
      wrap.appendChild(camDot);

      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [simulating, chapters]);

  /* ── Notify parent of changes ── */
  useEffect(() => {
    if (onMiniatureChange) {
      onMiniatureChange({
        file: thumbnailName,
        transition_frames: transFrames,
        chapters,
      });
    }
  }, [thumbnailName, transFrames, chapters, onMiniatureChange]);

  /* ── Segment options for dropdown ── */
  const segmentOptions = timeline.map((s) => ({
    value: s.id,
    label: `#${s.id} (${s.start.toFixed(1)}s)`,
  }));

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Config panel (left) */}
      <aside className="w-80 border-r border-gray-800 overflow-y-auto p-4 bg-gray-900">
        {/* Upload */}
        <div className="mb-4">
          <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
            📎 Miniature PNG
          </h3>
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-700 rounded-lg p-4 text-center cursor-pointer hover:border-amber-600 transition-colors"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg"
              onChange={handleFileUpload}
              className="hidden"
            />
            <div className="text-xs text-gray-400">
              <b className="text-gray-300">Cliquer pour uploader</b>
              <br />
              PNG ou JPG
              {thumbnailName && (
                <div className="text-amber-400 mt-1">{thumbnailName}</div>
              )}
            </div>
          </div>
        </div>

        {/* Chapters */}
        <div className="mb-4">
          <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
            📑 Chapitres
          </h3>
          <div className="text-xs text-gray-500 mb-2 leading-relaxed">
            Clique sur un chapitre pour le sélectionner.<br />
            Clique sur la miniature pour placer la balise caméra.
          </div>
          <div className="flex flex-col gap-2 mb-2">
            {chapters.length === 0 && (
              <div className="text-xs text-gray-600 p-2">Aucun chapitre — clique pour commencer.</div>
            )}
            {chapters.map((ch, idx) => (
              <div
                key={ch.id}
                onClick={() => setSelectedChapter(idx)}
                className={`p-2 rounded border cursor-pointer transition-colors ${
                  idx === selectedChapter
                    ? "border-amber-500 bg-amber-950/30"
                    : "border-gray-800 hover:border-gray-700"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                      idx === selectedChapter ? "bg-amber-500 text-black" : "bg-gray-700 text-gray-300"
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <input
                    type="text"
                    value={ch.label}
                    onChange={(e) => updateChapterLabel(idx, e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-0.5 text-xs text-gray-200"
                  />
                  <button
                    onClick={(e) => { e.stopPropagation(); removeChapter(idx); }}
                    className="text-gray-500 hover:text-red-400 text-sm"
                  >
                    ×
                  </button>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <select
                    value={ch.start_segment}
                    onChange={(e) => updateChapterSegment(idx, e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded px-1 py-0.5 text-xs text-gray-300"
                  >
                    {segmentOptions.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                  <span className={`text-xs ${ch.waypoint ? "text-green-400" : "text-gray-600"}`}>
                    {ch.waypoint ? `(${ch.waypoint.x.toFixed(2)}, ${ch.waypoint.y.toFixed(2)})` : "— pas de balise —"}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={addChapter}
            className="w-full py-1.5 border border-gray-700 rounded text-xs text-gray-400 hover:border-amber-600 hover:text-amber-400 transition-colors"
          >
            + Ajouter chapitre
          </button>
        </div>

        {/* Transition */}
        <div className="mb-4">
          <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
            🎥 Transition caméra
          </h3>
          <label className="text-xs text-gray-400 flex justify-between">
            <span>Durée</span>
            <span className="font-mono text-amber-400">{transFrames} frames</span>
          </label>
          <input
            type="range"
            min="15"
            max="90"
            step="5"
            value={transFrames}
            onChange={(e) => setTransFrames(parseInt(e.target.value))}
            className="w-full mt-1 accent-amber-500"
          />
        </div>

        {/* Camera simulation */}
        <div>
          <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
            ▶️ Aperçu caméra
          </h3>
          <button
            onClick={simulateCamera}
            disabled={simulating || chapters.filter((c) => c.waypoint).length < 2}
            className="w-full py-2 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-800 disabled:text-gray-600 rounded text-xs font-semibold transition-colors"
          >
            {simulating ? "⏳ Simulation..." : "▶ Simuler mouvement caméra"}
          </button>
        </div>
      </aside>

      {/* Canvas area (right) */}
      <div className="flex-1 overflow-auto bg-gray-950 flex flex-col items-center p-5 gap-4">
        {thumbnailURL ? (
          <div
            ref={canvasWrapRef}
            onClick={handleCanvasClick}
            className="relative border-2 border-amber-900 rounded-lg overflow-hidden cursor-crosshair bg-black"
            style={{ display: "inline-block" }}
          >
            <img
              src={thumbnailURL}
              alt="Miniature"
              className="block max-w-full max-h-[60vh] pointer-events-none"
            />
            {/* Waypoint dots */}
            {chapters.map((ch, idx) => {
              if (!ch.waypoint) return null;
              return (
                <div
                  key={ch.id}
                  onClick={(e) => { e.stopPropagation(); setSelectedChapter(idx); }}
                  className={`mini-dot absolute w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold cursor-pointer transition-transform hover:scale-120 ${
                    idx === selectedChapter
                      ? "bg-red-500 border-white z-20"
                      : "bg-amber-500 border-black z-10"
                  }`}
                  style={{
                    left: `${ch.waypoint.x * 100}%`,
                    top: `${ch.waypoint.y * 100}%`,
                    transform: "translate(-50%, -50%)",
                    border: "2px solid",
                    boxShadow: "0 0 8px rgba(0,0,0,0.8)",
                  }}
                >
                  {idx + 1}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-gray-600 text-sm text-center p-10">
            Uploade une miniature PNG pour commencer<br />
            à placer les balises caméra.
          </div>
        )}
      </div>
    </div>
  );
};
