import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const nm = (pkg) => path.resolve(__dirname, "node_modules", pkg);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@f03": path.resolve(__dirname, "../F03_SIGISMUND/CODEBASE/src"),
      // Force resolution des deps Remotion depuis F02 node_modules
      // (les composants F03 sont hors du project root)
      "remotion": nm("remotion"),
      "@remotion/player": nm("@remotion/player"),
      "@remotion/gif": nm("@remotion/gif"),
      "react": nm("react"),
      "react-dom": nm("react-dom"),
    },
  },
});
