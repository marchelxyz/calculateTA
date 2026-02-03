import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

function createConfig() {
  return defineConfig({
    plugins: [vue()],
    server: {
      proxy: {
        "/api": "http://localhost:8000",
      },
    },
    build: {
      outDir: "dist",
    },
  });
}

export default createConfig();
