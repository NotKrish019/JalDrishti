import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // three.js lives in the lazily-loaded DescentScene chunk (~140 kB gzip),
    // fetched only on the landing page after first paint.
    chunkSizeWarningLimit: 600,
  },
  server: {
    port: 5173,
    host: true,
  },
});
