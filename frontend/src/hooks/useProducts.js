/**
 * src/hooks/useProducts.js
 * ─────────────────────────
 * Custom React hook for fetching and managing the products list.
 *
 * TODO Phase 2: Replace with a proper data-fetching library
 *               (React Query / SWR) for caching, revalidation, and
 *               background refetching.
 */

import { useState, useEffect, useCallback } from 'react';
import { getProducts } from '@/api/products';

/**
 * @param {Object} options
 * @param {number} options.skip     - Pagination offset
 * @param {number} options.limit    - Page size
 * @param {string} options.platform - 'amazon' | 'flipkart' | undefined
 */
export function useProducts({ skip = 0, limit = 20, platform } = {}) {
  const [products, setProducts]   = useState([]);
  const [loading,  setLoading]    = useState(false);
  const [error,    setError]      = useState(null);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await getProducts({ skip, limit, platform });
      setProducts(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  }, [skip, limit, platform]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return { products, loading, error, refetch: fetchProducts };
}
