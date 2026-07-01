import React from "react";

/**
 * DeviceFrame — cadre simulant un appareil (PC ou mobile)
 * Props : label (string), aspect (CSS aspect-ratio), children (Player)
 */
export const DeviceFrame = ({ label, aspect, children }) => {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-sm text-gray-400 font-mono">{label}</span>
      <div
        className="border-2 border-gray-700 rounded-xl overflow-hidden bg-black shadow-2xl"
        style={{
          aspectRatio: aspect,
          width: aspect === "16/9" ? "100%" : "280px",
          maxWidth: "100%",
        }}
      >
        {children}
      </div>
    </div>
  );
};
