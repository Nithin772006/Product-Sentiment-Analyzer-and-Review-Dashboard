/**
 * src/api/client.js
 * ─────────────────
 * Configured Axios instance with:
 *   - Base URL from VITE_API_BASE_URL env variable (falls back to localhost:8000)
 *   - Global request/response interceptors for logging and error handling
 *   - 30-second timeout
 *
 * Usage:
 *   import apiClient from '@/api/client';
 *   const { data } = await apiClient.get('/api/v1/products');
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ── Request Interceptor ──────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    // TODO Phase 2: Attach JWT auth token if present
    // const token = localStorage.getItem('token');
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response Interceptor ─────────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Centralised error logging — Phase 2 can add toast notifications here
    const message = error.response?.data?.detail || error.message;
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url} → ${message}`);
    return Promise.reject(error);
  },
);

export default apiClient;
