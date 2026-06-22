import React from "react";
import { Img, OffthreadVideo } from "remotion";

// Bypass staticFile() — npm install delta en beta corrompt la résolution
// et retourne /public/file au lieu de /file → 404.
// Les fichiers sont dans public/ et servis à la racine par le serveur Remotion.
const sf = (f) => `/${f}`;

export const WorldNode = ({ imageFile, mediaType = "image" }) => {
  const src = sf(imageFile);
  const style = { width: "100%", height: "100%", objectFit: "cover" };

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
