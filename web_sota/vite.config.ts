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
    port: 10795,
    host: "127.0.0.1",
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:10794",
        changeOrigin: true,
      },
    },
  },
});
