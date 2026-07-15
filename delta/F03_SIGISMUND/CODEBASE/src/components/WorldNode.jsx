import React from "react";
import { Img, OffthreadVideo, staticFile } from "remotion";

// FIX v4: backgroundColor "#000" added to mask transparent pixels in F00 frames.
// Many F00 frames have alpha=0 pixels (extraction issue). The black background
// ensures capsules appear filled instead of showing holes.
export const WorldNode = ({ imageFile, mediaType = "image" }) => {
  const src = staticFile(imageFile);
  const style = { width: "100%", height: "100%", objectFit: "cover", backgroundColor: "#000" };

  if (mediaType === "gif") {
    // @remotion/gif — importé dynamiquement pour éviter l'erreur si absent
    try {
      const { Gif } = require("@remotion/gif");
      return <Gif src={src} style={style} fit="cover" />;
    } catch {
      return <Img src={src} style={style} />;
    }
  }

  if (mediaType === "video") {
    return <OffthreadVideo src={src} style={style} />;
  }

  return <Img src={src} style={style} />;
};
