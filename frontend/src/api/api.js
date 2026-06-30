import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 300_000, // 5 minutes — default for most endpoints
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let rawMessage = error.response?.data?.detail || error.message || "An unexpected error occurred";
    if (typeof rawMessage === "object") {
      if (Array.isArray(rawMessage)) {
        rawMessage = rawMessage.map(err => `${err.loc[err.loc.length - 1]}: ${err.msg}`).join(", ");
      } else {
        rawMessage = JSON.stringify(rawMessage);
      }
    }
    const errorData = {
      message: rawMessage,
      status: error.response?.status || 500,
    };
    console.error("[Axios API Error]", errorData);
    return Promise.reject(errorData);
  }
);

export const apiService = {
  // ── Health ─────────────────────────────────────────────────────────────────
  getHealth: () => api.get("/health"),

  // ── Authentication ─────────────────────────────────────────────────────────
  login: (username, password) =>
    api.post("/auth/login", { username, password }),

  register: (username, password, role = "user") =>
    api.post("/auth/register", { username, password, role }),

  // ── Search ─────────────────────────────────────────────────────────────────
  searchProducts: (q, skip = 0, limit = 20) => 
    api.get("/search", { params: { q, skip, limit } }),

  // ── Products CRUD ──────────────────────────────────────────────────────────
  getProducts: (skip = 0, limit = 12, sortBy = "created_at", order = "desc") =>
    api.get("/products", { params: { skip, limit, sort_by: sortBy, order } }),

  getProduct: (id) => api.get(`/products/${id}`),

  // Scraping can take 3–5 minutes — use a dedicated long timeout
  searchAndScrapeProduct: (productUrl, maxPages = 5) =>
    api.post("/products/search", { product_url: productUrl, max_pages: maxPages }, { timeout: 360_000 }),

  updateProduct: (id, payload) => api.put(`/products/${id}`, payload),

  deleteProduct: (id) => api.delete(`/products/${id}`),

  // ── Reviews & Sentiments ───────────────────────────────────────────────────
  getProductReviews: (productId, params = {}) =>
    api.get(`/reviews/product/${productId}`, { params }),

  getProductSentiments: (productId, params = {}) =>
    api.get(`/sentiments/product/${productId}`, { params }),

  // ── Analytics ──────────────────────────────────────────────────────────────
  getProductAnalytics: (productId) => api.get(`/analytics/product/${productId}`),

  getDashboardSummary: () => api.get("/analytics/dashboard/summary"),

  getDashboardCharts: () => api.get("/analytics/dashboard/charts"),

  getDashboardTrends: (timeframe = "monthly") =>
    api.get("/analytics/dashboard/trends", { params: { timeframe } }),

  getDashboardKeywords: (limit = 15) =>
    api.get("/analytics/dashboard/keywords", { params: { limit } }),

  // ── Export URLs (returned directly as absolute paths) ──────────────────────
  getExportCsvUrl: (id) => `${BASE_URL}/reports/export/csv/${id}`,
  getExportExcelUrl: (id) => `${BASE_URL}/reports/export/excel/${id}`,
  getExportPdfUrl: (id) => `${BASE_URL}/reports/export/pdf/${id}`,
};

export default apiService;
