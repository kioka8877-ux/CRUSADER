import React from "react";
import { Img, OffthreadVideo } from "remotion";

/**
 * WorldNode.jsx — PREVIEW MODE
 * Pas de staticFile() — chemins relatifs "./" pour fonctionner en export HTML
 * Pas de require() pour @remotion/gif — utilise <Img> pour tout
 */
export const WorldNode = ({ imageFile, mediaType = "image" }) => {
  const src = "./" + imageFile;
  const style = { width: "100%", height: "100%", objectFit: "cover" };

  if (mediaType === "video") {
    return <OffthreadVideo src={src} style={style} />;
  }

  // gif et image utilisent tous deux <Img>
  return <Img src={src} style={style} />;
};
