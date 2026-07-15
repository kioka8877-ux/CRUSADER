import React from "react";

/**
 * ControlPanel — sliders & selects pour ajuster les params du roadmap.style
 * Props : style (current), onChange(key, value)
 */

const Slider = ({ label, paramKey, value, min, max, step, onChange }) => (
  <div className="mb-3">
    <label className="text-xs text-gray-400 flex justify-between">
      <span>{label}</span>
      <span className="font-mono text-amber-400">{value}</span>
    </label>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(paramKey, parseFloat(e.target.value))}
      className="w-full mt-1 accent-amber-500"
    />
  </div>
);

const ColorPicker = ({ label, paramKey, value, onChange }) => (
  <div className="mb-3 flex items-center gap-2">
    <input
      type="color"
      value={value}
      onChange={(e) => onChange(paramKey, e.target.value)}
      className="w-8 h-8 rounded border border-gray-600 cursor-pointer"
    />
    <span className="text-xs text-gray-400">{label}</span>
    <span className="text-xs font-mono text-amber-400 ml-auto">{value}</span>
  </div>
);

const Select = ({ label, paramKey, value, options, onChange }) => (
  <div className="mb-3">
    <label className="text-xs text-gray-400">{label}</label>
    <select
      value={value}
      onChange={(e) => onChange(paramKey, e.target.value)}
      className="w-full mt-1 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  </div>
);

const SectionTitle = ({ children }) => (
  <h3 className="text-xs font-bold uppercase text-gray-500 tracking-wider mt-5 mb-2 border-b border-gray-800 pb-1">
    {children}
  </h3>
);

export const ControlPanel = ({ style, onChange }) => {
  const s = style;
  const FONTS = [
    "Cinzel", "Playfair Display", "Lato", "Oswald",
    "Roboto Slab", "Inter", "Arial Black", "Helvetica",
  ];

  // Backgrounds PNG disponibles dans le projet
  const BACKGROUNDS = [
    { label: "🎨 Couleur unie", value: "solid" },
    { label: "📄 Papier froissé", value: "bg_paper_crumpled.png" },
    { label: "📃 Papier neuf", value: "bg_paper_new.png" },
    { label: "📜 Papyrus ancien", value: "bg_papyrus_old.png" },
    { label: "🔲 Grille sombre", value: "bg_grid_dark.png" },
    { label: "🔵 Bleu uni", value: "bg_solid_blue.png" },
  ];

  // Détermine la valeur actuelle du background
  const currentBg = s.background_image && s.background_image !== "solid"
    ? s.background_image
    : "solid";

  return (
    <div>
      <SectionTitle>📐 Capsules (Worlds)</SectionTitle>
      <Slider label="Taille visuel actif" paramKey="world_scale" value={s.world_scale ?? 0.7} min={0.2} max={1} step={0.05} onChange={onChange} />
      <Slider label="Taille visuel N+1" paramKey="world_next_scale" value={s.world_next_scale ?? 0.35} min={0.1} max={1} step={0.05} onChange={onChange} />
      <Slider label="Opacité visuel actif" paramKey="world_opacity" value={s.world_opacity ?? 1} min={0} max={1} step={0.05} onChange={onChange} />
      <Slider label="Opacité visuel N+1" paramKey="world_next_opacity" value={s.world_next_opacity ?? 0.3} min={0} max={1} step={0.01} onChange={onChange} />

      <SectionTitle>🎥 Caméra sinusoïdale</SectionTitle>
      <Slider label="Amplitude (px)" paramKey="camera_amplitude" value={s.camera_amplitude ?? 200} min={0} max={500} step={10} onChange={onChange} />
      <Slider label="Espacement (px)" paramKey="camera_spacing" value={s.camera_spacing ?? 1500} min={500} max={3000} step={50} onChange={onChange} />

      <SectionTitle>🖼️ Papier peint (Background)</SectionTitle>
      <Select
        label="Choisir le fond"
        paramKey="background_image"
        value={currentBg}
        options={BACKGROUNDS}
        onChange={onChange}
      />
      {currentBg === "solid" && (
        <ColorPicker label="Couleur fond" paramKey="background_color" value={s.background_color ?? "#F5F0E8"} onChange={onChange} />
      )}
      <Slider label="Scale fond" paramKey="background_scale" value={s.background_scale ?? 1} min={0.5} max={2} step={0.05} onChange={onChange} />

      <SectionTitle>📝 Sous-titres</SectionTitle>
      <Select label="Police" paramKey="subtitle_font" value={s.subtitle_font ?? s.font_primary ?? "Cinzel"} options={FONTS.map(f => ({ label: f, value: f }))} onChange={onChange} />
      <Slider label="Taille" paramKey="subtitle_size" value={parseInt(s.subtitle_size, 10) || 44} min={16} max={80} step={2} onChange={onChange} />
      <ColorPicker label="Couleur" paramKey="subtitle_color" value={s.subtitle_color ?? "#FFFFFF"} onChange={onChange} />
      <ColorPicker label="Couleur accent" paramKey="accent_color" value={s.accent_color ?? "#FFD700"} onChange={onChange} />
      <Select label="Position" paramKey="subtitle_position" value={s.subtitle_position ?? "bottom"} options={[{label:"Haut",value:"top"},{label:"Centre",value:"center"},{label:"Bas",value:"bottom"}]} onChange={onChange} />
      <Select label="Alignement" paramKey="subtitle_align" value={s.subtitle_align ?? "center"} options={[{label:"Gauche",value:"left"},{label:"Centre",value:"center"},{label:"Droite",value:"right"}]} onChange={onChange} />

      <SectionTitle>🏷️ Titres des worlds</SectionTitle>
      <Select label="Visible" paramKey="world_title_visible" value={s.world_title_visible ? "true" : "false"} options={[{label:"Non",value:"false"},{label:"Oui",value:"true"}]} onChange={(k, v) => onChange(k, v === "true")} />
      <Select label="Position" paramKey="world_title_position" value={s.world_title_position ?? "left"} options={[{label:"Gauche",value:"left"},{label:"Droite",value:"right"}]} onChange={onChange} />
      <Select label="Police" paramKey="world_title_font" value={s.world_title_font ?? s.font_primary ?? "Cinzel"} options={FONTS.map(f => ({ label: f, value: f }))} onChange={onChange} />
      <Slider label="Taille" paramKey="world_title_size" value={s.world_title_size ?? 28} min={14} max={60} step={2} onChange={onChange} />
      <ColorPicker label="Couleur" paramKey="world_title_color" value={s.world_title_color ?? "#FFFFFF"} onChange={onChange} />

      <SectionTitle>🎨 Grain & Vignette</SectionTitle>
      <Slider label="Grain" paramKey="grain_intensity" value={s.grain_intensity ?? 0.15} min={0} max={0.5} step={0.01} onChange={onChange} />
      <Select label="Vignette" paramKey="vignette" value={s.vignette ? "true" : "false"} options={[{label:"Non",value:"false"},{label:"Oui",value:"true"}]} onChange={(k, v) => onChange(k, v === "true")} />
    </div>
  );
};
