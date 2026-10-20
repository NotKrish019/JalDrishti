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
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/analyze': 'http://127.0.0.1:8000',
      '/images': 'http://127.0.0.1:8000',
      '/knowledge': 'http://127.0.0.1:8000',
      '/material-compatibility': 'http://127.0.0.1:8000',
      '/restore': 'http://127.0.0.1:8000',
      '/engineering': 'http://127.0.0.1:8000',
      '/vision': 'http://127.0.0.1:8000',
      '/inspections': 'http://127.0.0.1:8000',
    },
  },
});
