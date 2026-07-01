import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@f03": path.resolve(
        __dirname,
        "../F03_SIGISMUND/CODEBASE/src"
      ),
    },
  },
});
