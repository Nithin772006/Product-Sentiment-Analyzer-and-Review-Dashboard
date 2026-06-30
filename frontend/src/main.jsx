/**
 * src/main.jsx
 * ─────────────
 * Application entry point.
 * Mounts the React tree into the #root DOM node.
 */

import { StrictMode } from 'react';
import { createRoot }  from 'react-dom/client';
import '@/styles/index.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
