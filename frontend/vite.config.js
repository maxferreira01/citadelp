import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// O design system vive em ../design-system (fora da raiz do Vite) e é importado
// direto da fonte — uma verdade só, sem cópia em src/.
const designSystem = fileURLToPath(new URL("../design-system", import.meta.url));
const repoRoot = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@ds": designSystem },
    // os componentes do DS fazem `import React from 'react'` de fora de frontend/;
    // dedupe força a resolução a partir daqui (uma cópia só de react/react-dom)
    dedupe: ["react", "react-dom"],
  },
  server: {
    fs: { allow: [repoRoot] },
    proxy: {
      // frontend chama /api/* → CITADEL API (uvicorn :5533)
      "/api": { target: "http://localhost:5533", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
});
