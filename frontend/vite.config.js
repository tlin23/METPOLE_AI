import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path, { dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  // Load environment variables from the appropriate .env file
  const env = loadEnv(mode, path.resolve(__dirname));

  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": {
          target: env.VITE_BACKEND_URL,
          changeOrigin: true,
        },
        "/admin": {
          target: env.VITE_BACKEND_URL,
          changeOrigin: true,
          ws: false,
        },
      },
    },
  };
});
