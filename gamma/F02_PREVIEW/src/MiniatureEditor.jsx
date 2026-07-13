import React, { useState, useRef, useEffect } from "react";

/**
 * MiniatureEditor v4 — Mini Créateur avec sélecteur rectangle + waypoints
 *
 * Workflow par chapitre:
 * 1. Upload image
 * 2. Dessiner un rectangle (sélection de la zone à couper)
 * 3. Placer les waypoints DANS le rectangle (où la caméra passe)
 *    - Chapitre 1: 1 waypoint (zoom in)
 *    - Chapitres suivants: 2 waypoints (pan wp1 → wp2)
 * 4. Découper → fragment PNG (Canvas API, sans perte)
 */
export const MiniatureEditor = ({ timeline, onMiniatureChange, onThumbnailUpload, introDuration = 90, zoomLevel = 2.5, onIntroDurationChange, onZoomLevelChange }) => {
  const [numChapters, setNumChapters] = useState(0);
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState(-1);
  const [transFrames, setTransFrames] = useState(45);
  const fileInputRef = useRef(null);
  const imgRefs = useRef({});

  // Drawing state
  const [drawing, setDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState(null);
  const [drawCurrent, setDrawCurrent] = useState(null);
  const canvasWrapRef = useRef(null);

  /* ── Générer les chapitres ── */
  const generateChapters = () => {
    const n = Math.max(1, Math.min(50, numChapters));
    const newChapters = [];
    for (let i = 0; i < n; i++) {
      const seg = timeline.length > i ? timeline[i].id : (timeline[0]?.id || 1);
      newChapters.push({
        id: i + 1,
        label: `Chapitre ${i + 1}`,
        start_segment: seg,
        imageURL: null,
        imageName: "",
        crop: null,        // {x1, y1, x2, y2} normalized — la zone sélectionnée
        waypoints: [],     // [{x, y}, ...] DANS le crop (normalized par rapport au crop)
        fragment: null,    // data URL PNG découpé
        isDiagonal: false,
      });
    }
    setChapters(newChapters);
    setSelectedChapter(0);
  };

  /* ── Upload image ── */
  const handleFileUpload = (e, idx) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataURL = ev.target.result;
      setChapters(prev => prev.map((c, i) =>
        i === idx ? { ...c, imageURL: dataURL, imageName: file.name, crop: null, waypoints: [], fragment: null } : c
      ));
      const img = new Image();
      img.onload = () => { imgRefs.current[idx] = img; };
      img.src = dataURL;
      if (onThumbnailUpload && idx === 0) onThumbnailUpload(dataURL, file.name);
    };
    reader.readAsDataURL(file);
  };

  /* ── Dessin du rectangle de sélection ── */
  const handleMouseDown = (e) => {
    if (selectedChapter < 0) return;
    const ch = chapters[selectedChapter];
    if (!ch?.imageURL) return;
    // Si on clique sur un waypoint existant, ne pas dessiner
    if (e.target.classList.contains("wp-dot") || e.target.closest(".wp-dot")) return;

    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    setDrawing(true);
    setDrawStart({ x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) });
    setDrawCurrent({ x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) });
  };

  const handleMouseMove = (e) => {
    if (!drawing) return;
    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setDrawCurrent({ x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) });
  };

  const handleMouseUp = () => {
    if (!drawing || !drawStart || !drawCurrent) return;
    setDrawing(false);

    const crop = {
      x1: Math.min(drawStart.x, drawCurrent.x),
      y1: Math.min(drawStart.y, drawCurrent.y),
      x2: Math.max(drawStart.x, drawCurrent.x),
      y2: Math.max(drawStart.y, drawCurrent.y),
    };

    // Minimum size
    if (Math.abs(crop.x2 - crop.x1) < 0.05 || Math.abs(crop.y2 - crop.y1) < 0.05) {
      setDrawStart(null);
      setDrawCurrent(null);
      return;
    }

    // Sauvegarder le crop et reset waypoints (ils doivent être DANS le crop)
    setChapters(prev => prev.map((c, i) =>
      i === selectedChapter ? { ...c, crop, waypoints: [], fragment: null } : c
    ));
    setDrawStart(null);
    setDrawCurrent(null);
  };

  /* ── Clic sur l'image → placer waypoint (chapitre 1: pas de crop, clic direct) ── */
  const handleImageClickDirect = (e) => {
    if (selectedChapter < 0) return;
    const ch = chapters[selectedChapter];
    if (!ch?.imageURL) return;
    if (e.target.classList.contains("wp-dot") || e.target.closest(".wp-dot")) return;

    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    // Chapitre 1: 1 waypoint, pas de crop, fragment = image complète
    if (selectedChapter === 0) {
      setChapters(prev => prev.map((c, i) =>
        i === 0 ? { ...c, waypoints: [{ x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) }] } : c
      ));
    }
  };

  /* ── Clic DANS le rectangle → placer waypoint ── */
  const handleCropClick = (e) => {
    const ch = chapters[selectedChapter];
    if (!ch?.crop) return;

    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) / rect.width;
    const clickY = (e.clientY - rect.top) / rect.height;

    // Vérifier que le clic est DANS le crop
    if (clickX < ch.crop.x1 || clickX > ch.crop.x2 || clickY < ch.crop.y1 || clickY > ch.crop.y2) return;

    // Convertir en coordonnées relatives au crop (0-1 dans le crop)
    const wpX = (clickX - ch.crop.x1) / (ch.crop.x2 - ch.crop.x1);
    const wpY = (clickY - ch.crop.y1) / (ch.crop.y2 - ch.crop.y1);

    const isFirst = selectedChapter === 0;
    const maxPoints = isFirst ? 1 : 2;

    setChapters(prev => prev.map((c, i) => {
      if (i !== selectedChapter) return c;
      let wps = [...c.waypoints];
      if (wps.length >= maxPoints) {
        wps = [{ x: wpX, y: wpY }];
      } else {
        wps.push({ x: wpX, y: wpY });
      }
      return { ...c, waypoints: wps, fragment: null };
    }));
  };

  /* ── Découper le fragment ── */
  const cropFragment = (idx) => {
    const ch = chapters[idx];
    if (!ch || !ch.imageURL) return;

    const img = imgRefs.current[idx];
    if (!img) {
      const img2 = new Image();
      img2.onload = () => { imgRefs.current[idx] = img2; cropFragment(idx); };
      img2.src = ch.imageURL;
      return;
    }

    // Chapitre 1: pas de crop, fragment = image complète
    if (idx === 0 || !ch.crop) {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      const fragmentURL = canvas.toDataURL("image/png");
      setChapters(prev => prev.map((c, i) => i === idx ? { ...c, fragment: fragmentURL } : c));
      return;
    }

    // Chapitres suivants: découper selon le crop
    const imgW = img.naturalWidth;
    const imgH = img.naturalHeight;

    // Coordonnées du crop en pixels
    const sx = ch.crop.x1 * imgW;
    const sy = ch.crop.y1 * imgH;
    const sw = (ch.crop.x2 - ch.crop.x1) * imgW;
    const sh = (ch.crop.y2 - ch.crop.y1) * imgH;

    // Canvas découpe — PNG sans perte
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(sw);
    canvas.height = Math.round(sh);
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);

    const fragmentURL = canvas.toDataURL("image/png");

    setChapters(prev => prev.map((c, i) =>
      i === idx ? { ...c, fragment: fragmentURL } : c
    ));
  };

  /* ── Helpers ── */
  const updateLabel = (idx, label) => setChapters(prev => prev.map((c, i) => (i === idx ? { ...c, label } : c)));
  const updateSegment = (idx, segId) => setChapters(prev => prev.map((c, i) => (i === idx ? { ...c, start_segment: parseInt(segId) } : c)));
  const toggleDiagonal = (idx) => setChapters(prev => prev.map((c, i) => (i === idx ? { ...c, isDiagonal: !c.isDiagonal } : c)));
  const resetCrop = (idx) => setChapters(prev => prev.map((c, i) => (i === idx ? { ...c, crop: null, waypoints: [], fragment: null } : c)));

  /* ── Notify parent ── */
  useEffect(() => {
    if (onMiniatureChange) {
      onMiniatureChange({
        file: chapters[0]?.imageName || null,
        transition_frames: transFrames,
        chapters,
        thumbnailURL: chapters[0]?.imageURL || null,
      });
    }
  }, [chapters, transFrames, onMiniatureChange]);

  const segmentOptions = timeline.map(s => ({ value: s.id, label: `#${s.id} (${s.start.toFixed(1)}s)` }));

  // === Drawing rectangle visuel ===
  const drawRect = drawStart && drawCurrent ? {
    left: `${Math.min(drawStart.x, drawCurrent.x) * 100}%`,
    top: `${Math.min(drawStart.y, drawCurrent.y) * 100}%`,
    width: `${Math.abs(drawCurrent.x - drawStart.x) * 100}%`,
    height: `${Math.abs(drawCurrent.y - drawStart.y) * 100}%`,
  } : null;

  const ch = selectedChapter >= 0 ? chapters[selectedChapter] : null;
  const isFirst = selectedChapter === 0;
  const maxPoints = isFirst ? 1 : 2;

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Panel gauche */}
      <aside className="w-96 border-r border-gray-800 overflow-y-auto p-4 bg-gray-900">
        {chapters.length === 0 ? (
          <div className="mb-4">
            <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
              📋 Étape 1 — Nombre de chapitres
            </h3>
            <div className="flex items-center gap-2">
              <input type="number" min="1" max="50" value={numChapters || ""}
                onChange={(e) => setNumChapters(parseInt(e.target.value) || 0)}
                placeholder="Ex: 17"
                className="w-24 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-200" />
              <button onClick={generateChapters} disabled={numChapters < 1}
                className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-semibold">
                Générer
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">Entre le nombre de chapitres, puis clique sur Générer.</p>
          </div>
        ) : (
          <>
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider border-b border-gray-800 pb-1 flex-1">
                  📑 {chapters.length} chapitres
                </h3>
                <button onClick={() => { setChapters([]); setNumChapters(0); setSelectedChapter(-1); }}
                  className="text-xs text-gray-500 hover:text-red-400 ml-2">↻ Recommencer</button>
              </div>
              <div className="flex flex-col gap-2 max-h-[35vh] overflow-y-auto">
                {chapters.map((c, idx) => (
                  <div key={c.id} onClick={() => setSelectedChapter(idx)}
                    className={`p-2 rounded border cursor-pointer transition-colors ${
                      idx === selectedChapter ? "border-amber-500 bg-amber-950/30" : "border-gray-800 hover:border-gray-700"
                    }`}>
                    <div className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                        idx === selectedChapter ? "bg-amber-500 text-black" : "bg-gray-700 text-gray-300"}`}>{idx + 1}</span>
                      <input type="text" value={c.label} onChange={(e) => updateLabel(idx, e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-0.5 text-xs text-gray-200" />
                      {c.fragment && <span className="text-green-400 text-xs">✓</span>}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <select value={c.start_segment} onChange={(e) => updateSegment(idx, e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 bg-gray-800 border border-gray-700 rounded px-1 py-0.5 text-xs text-gray-300">
                        {segmentOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                      {idx > 0 && (
                        <label className="flex items-center gap-1 text-xs text-gray-500" onClick={(e) => e.stopPropagation()}>
                          <input type="checkbox" checked={c.isDiagonal} onChange={() => toggleDiagonal(idx)} className="accent-amber-500" />
                          oblique
                        </label>
                      )}
                    </div>
                    {c.fragment && (
                      <div className="mt-2 flex items-center gap-2">
                        <img src={c.fragment} alt="fragment" className="w-16 h-10 object-cover rounded border border-gray-700" />
                        <span className="text-xs text-green-400">Fragment prêt</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Sliders */}
            <div className="mb-4">
              <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-2 border-b border-gray-800 pb-1">
                🎬 Intro Video Finale
              </h3>
              <label className="text-xs text-gray-400 flex justify-between">
                <span>Durée intro</span>
                <span className="font-mono text-amber-400">{(introDuration / 30).toFixed(1)}s ({introDuration}f)</span>
              </label>
              <input type="range" min="30" max="150" step="15" value={introDuration}
                onChange={(e) => onIntroDurationChange && onIntroDurationChange(parseInt(e.target.value))}
                className="w-full mt-1 accent-amber-500" />
              <label className="text-xs text-gray-400 flex justify-between mt-3">
                <span>Degré zoom (ch.1)</span>
                <span className="font-mono text-amber-400">{zoomLevel}×</span>
              </label>
              <input type="range" min="1.5" max="5" step="0.5" value={zoomLevel}
                onChange={(e) => onZoomLevelChange && onZoomLevelChange(parseFloat(e.target.value))}
                className="w-full mt-1 accent-amber-500" />
            </div>
          </>
        )}
      </aside>

      {/* Zone d'édition (droite) */}
      <div className="flex-1 overflow-auto bg-gray-950 flex flex-col items-center p-5 gap-4">
        {ch && ch.imageURL ? (
          <>
            {/* Instructions */}
            <div className="bg-gray-900 rounded-lg p-3 w-full max-w-3xl">
              <h3 className="text-sm font-bold text-amber-400 mb-1">
                Chapitre {selectedChapter + 1} {isFirst ? "— Zoom in" : ch.isDiagonal ? "— Ligne oblique" : "— Pan"}
              </h3>
              <p className="text-xs text-gray-400">
                {isFirst
                  ? "Clique sur l'image pour placer le waypoint (zoom in), puis clique sur ✂️ Découper"
                  : !ch.crop
                    ? "Étape 1: Dessine un rectangle sur l'image pour sélectionner la zone à couper (click-drag)"
                    : ch.waypoints.length < maxPoints
                      ? `Étape 2: Clique DANS le rectangle pour placer le waypoint ${ch.waypoints.length + 1}/${maxPoints}`
                      : "Étape 3: Clique sur ✂️ Découper pour générer le fragment"}
              </p>
            </div>

            {/* Image avec sélecteur */}
            <div
              ref={canvasWrapRef}
              onMouseDown={isFirst ? undefined : handleMouseDown}
              onMouseMove={isFirst ? undefined : handleMouseMove}
              onMouseUp={isFirst ? undefined : handleMouseUp}
              onMouseLeave={isFirst ? undefined : handleMouseUp}
              onClick={isFirst ? handleImageClickDirect : undefined}
              className="relative border-2 border-amber-900 rounded-lg overflow-hidden bg-black"
              style={{ display: "inline-block", cursor: "crosshair" }}
            >
              <img src={ch.imageURL} alt="Miniature" className="block max-w-full max-h-[45vh] pointer-events-none select-none" />

              {/* Waypoint pour le chapitre 1 (pas de crop, directement sur l'image) */}
              {isFirst && ch.waypoints.map((wp, i) => (
                <div
                  key={i}
                  className="wp-dot absolute w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{
                    left: `${wp.x * 100}%`,
                    top: `${wp.y * 100}%`,
                    transform: "translate(-50%, -50%)",
                    background: "#fbbf24",
                    color: "#000",
                    border: "2px solid #000",
                    boxShadow: "0 0 8px rgba(0,0,0,0.8)",
                    zIndex: 20,
                    cursor: "pointer",
                  }}
                >
                  {i + 1}
                </div>
              ))}

              {/* Rectangle de sélection (crop) — chapitres 2+ seulement */}
              {ch.crop && !isFirst && (
                <div
                  className="absolute border-2 border-amber-500 bg-amber-500/10"
                  style={{
                    left: `${ch.crop.x1 * 100}%`,
                    top: `${ch.crop.y1 * 100}%`,
                    width: `${(ch.crop.x2 - ch.crop.x1) * 100}%`,
                    height: `${(ch.crop.y2 - ch.crop.y1) * 100}%`,
                    zIndex: 10,
                  }}
                  onClick={handleCropClick}
                >
                  {/* Label du crop */}
                  <span className="absolute -top-5 left-0 text-xs font-bold px-1 rounded bg-amber-500 text-black">
                    Zone à couper
                  </span>

                  {/* Waypoints DANS le crop */}
                  {ch.waypoints.map((wp, i) => (
                    <div
                      key={i}
                      className="wp-dot absolute w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                      style={{
                        left: `${wp.x * 100}%`,
                        top: `${wp.y * 100}%`,
                        transform: "translate(-50%, -50%)",
                        background: i === 0 ? "#fbbf24" : "#3b82f6",
                        color: "#000",
                        border: "2px solid #000",
                        boxShadow: "0 0 8px rgba(0,0,0,0.8)",
                        zIndex: 20,
                        cursor: "pointer",
                      }}
                    >
                      {i + 1}
                    </div>
                  ))}

                  {/* Ligne entre wp1 et wp2 */}
                  {ch.waypoints.length === 2 && (
                    <svg className="absolute inset-0 pointer-events-none" style={{ width: "100%", height: "100%", zIndex: 15 }}>
                      <line
                        x1={`${ch.waypoints[0].x * 100}%`}
                        y1={`${ch.waypoints[0].y * 100}%`}
                        x2={`${ch.waypoints[1].x * 100}%`}
                        y2={`${ch.waypoints[1].y * 100}%`}
                        stroke="#3b82f6"
                        strokeWidth="2"
                        strokeDasharray="5,3"
                      />
                    </svg>
                  )}
                </div>
              )}

              {/* Rectangle en cours de dessin */}
              {drawRect && (
                <div className="absolute border-2 border-dashed border-blue-400 bg-blue-400/10 pointer-events-none"
                  style={{ ...drawRect, zIndex: 30 }} />
              )}
            </div>

            {/* Boutons d'action */}
            <div className="flex items-center gap-3">
              <input ref={fileInputRef} type="file" accept="image/png,image/jpeg" onChange={(e) => handleFileUpload(e, selectedChapter)} className="hidden" />
              <button onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-sm text-gray-300">
                📎 {ch.imageName}
              </button>

              {ch.crop && (
                <button onClick={() => resetCrop(selectedChapter)}
                  className="px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-sm text-gray-400">
                  ↻ Refaire la sélection
                </button>
              )}

              {ch.crop && ch.waypoints.length >= maxPoints && !ch.fragment && !isFirst && (
                <button onClick={() => cropFragment(selectedChapter)}
                  className="px-6 py-2 bg-green-700 hover:bg-green-600 rounded text-sm font-semibold">
                  ✂️ Découper le fragment
                </button>
              )}

              {/* Bouton découper pour le chapitre 1 (pas besoin de crop) */}
              {isFirst && ch.waypoints.length >= 1 && !ch.fragment && (
                <button onClick={() => cropFragment(selectedChapter)}
                  className="px-6 py-2 bg-green-700 hover:bg-green-600 rounded text-sm font-semibold">
                  ✂️ Valider le fragment
                </button>
              )}
            </div>

            {/* Aperçu du fragment */}
            {ch.fragment && (
              <div className="flex flex-col items-center gap-2">
                <p className="text-xs text-green-400">✓ Fragment découpé (PNG sans perte)</p>
                <img src={ch.fragment} alt="Fragment" className="max-w-full max-h-[20vh] rounded border-2 border-green-700" />
                <button onClick={() => cropFragment(selectedChapter)} className="text-xs text-gray-500 hover:text-amber-400">
                  ↻ Redécouper
                </button>
              </div>
            )}
          </>
        ) : ch && !ch.imageURL ? (
          <>
            <div className="bg-gray-900 rounded-lg p-3 w-full max-w-3xl">
              <h3 className="text-sm font-bold text-amber-400 mb-1">Chapitre {selectedChapter + 1}</h3>
              <p className="text-xs text-gray-400">Étape 0: Uploade l'image pour ce chapitre</p>
            </div>
            <input ref={fileInputRef} type="file" accept="image/png,image/jpeg" onChange={(e) => handleFileUpload(e, selectedChapter)} className="hidden" />
            <button onClick={() => fileInputRef.current?.click()}
              className="px-6 py-3 bg-amber-600 hover:bg-amber-500 rounded text-sm font-semibold">
              📎 Uploader l'image
            </button>
          </>
        ) : (
          <div className="text-gray-600 text-sm text-center p-10">
            Entre le nombre de chapitres et clique sur Générer pour commencer.
          </div>
        )}
      </div>
    </div>
  );
};
