import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 10838,
    host: "127.0.0.1",
    proxy: {
      "/api/v1": {
        // Must match web_sota/start.ps1 $BackendPort (and uvicorn --port); not fleet 10794
        target: "http://127.0.0.1:10839",
        changeOrigin: true,
      },
    },
  },
});
