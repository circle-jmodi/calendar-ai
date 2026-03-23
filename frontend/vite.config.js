import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/auth": "http://backend:8000",
      "/calendar": "http://backend:8000",
      "/preferences": "http://backend:8000",
      "/optimize": "http://backend:8000",
      "/schedule": "http://backend:8000",
      "/slack": "http://backend:8000",
    },
  },
});
