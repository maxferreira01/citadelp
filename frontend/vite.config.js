import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // frontend chama /api/* → CITADEL API (uvicorn :5533)
      "/api": { target: "http://localhost:5533", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
});
