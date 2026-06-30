import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      // Allow absolute imports from src/, e.g. import Foo from '@/components/Foo'
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    host: true, // listen on 0.0.0.0 so Docker can expose the port

    // Proxy API requests to the FastAPI backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        // Split vendor chunks for better caching
        manualChunks: {
          react: ['react', 'react-dom'],
          router: ['react-router-dom'],
          charts: ['recharts'],
          axios: ['axios'],
        },
      },
    },
  },
});
