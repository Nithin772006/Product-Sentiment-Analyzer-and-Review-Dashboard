/**
 * src/api/products.js
 * ────────────────────
 * All product-related API calls.
 * Each function maps 1-to-1 with a backend REST endpoint.
 *
 * TODO Phase 2: Replace placeholder comments with real calls once
 *               the backend implements those routes.
 */

import apiClient from './client';

/**
 * Fetch paginated product list.
 * @param {Object} params - { skip, limit, platform }
 */
export const getProducts = (params = {}) =>
  apiClient.get('/api/v1/products', { params });

/**
 * Add a new product for tracking.
 * @param {Object} payload - ProductCreate schema
 */
export const createProduct = (payload) =>
  apiClient.post('/api/v1/products', payload);

/**
 * Trigger scrape + sentiment analysis job.
 * @param {string} url - Product page URL
 * @param {string} platform - 'amazon' | 'flipkart'
 * @param {number} maxPages - Number of review pages to scrape
 */
export const triggerScrape = (url, platform, maxPages = 5) =>
  apiClient.post('/api/v1/products/scrape', null, {
    params: { url, platform, max_pages: maxPages },
  });

/**
 * Get a single product by ID.
 * @param {string} productId
 */
export const getProductById = (productId) =>
  apiClient.get(`/api/v1/products/${productId}`);

/**
 * Get paginated reviews for a product.
 * @param {string} productId
 * @param {Object} params - { skip, limit, sentiment }
 */
export const getProductReviews = (productId, params = {}) =>
  apiClient.get(`/api/v1/products/${productId}/reviews`, { params });

/**
 * Get the aggregated sentiment summary for a product.
 * @param {string} productId
 */
export const getSentimentSummary = (productId) =>
  apiClient.get(`/api/v1/products/${productId}/sentiment`);

/**
 * Health check — used to verify API connectivity on load.
 */
export const getHealth = () => apiClient.get('/health');
