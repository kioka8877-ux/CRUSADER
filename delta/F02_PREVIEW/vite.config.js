import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { viteSingleFile } = require("vite-plugin-singlefile");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nm = (pkg) => path.resolve(__dirname, "node_modules", pkg);
const f03src = path.resolve(__dirname, "../F03_SIGISMUND/CODEBASE/src");

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss(), viteSingleFile()],
  resolve: {
    alias: {
      "@f03": f03src,
      "remotion": nm("remotion"),
      "@remotion/player": nm("@remotion/player"),
      "@remotion/gif": nm("@remotion/gif"),
      "react": nm("react"),
      "react-dom": nm("react-dom"),
    },
  },
  build: {
    assetsInlineLimit: 100000000,
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        format: "iife",
        inlineDynamicImports: true,
      },
    },
  },
});
