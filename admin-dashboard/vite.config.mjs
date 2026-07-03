import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: "@movu/ui/styles.css", replacement: path.resolve("../packages/ui/src/styles.css") },
      { find: "@movu/ui", replacement: path.resolve("../packages/ui/src/components") }
    ]
  },
  server: {
    port: 5173
  }
});
