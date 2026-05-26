import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In a container the backend is reachable by service name; on the host it is
// localhost. Polling is needed for HMR when source is bind-mounted from Windows.
const apiTarget = process.env.VITE_API_PROXY || "http://127.0.0.1:8000";
const usePolling = process.env.VITE_USE_POLLING === "true";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": apiTarget
    },
    ...(usePolling ? { watch: { usePolling: true } } : {})
  }
});

