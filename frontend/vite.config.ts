import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" makes the build work from any path: its own domain, a portfolio
// sub-folder, an iframe, or FastAPI at /app.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
