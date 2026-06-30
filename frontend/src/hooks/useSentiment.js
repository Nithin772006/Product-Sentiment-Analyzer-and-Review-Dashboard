/**
 * src/hooks/useSentiment.js
 * ──────────────────────────
 * Custom React hook for fetching sentiment summary data for a product.
 *
 * TODO Phase 2: Integrate React Query for stale-while-revalidate caching.
 */

import { useState, useEffect } from 'react';
import { getSentimentSummary } from '@/api/products';

/**
 * @param {string|null} productId - MongoDB ObjectId string
 */
export function useSentiment(productId) {
  const [sentiment, setSentiment] = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);

  useEffect(() => {
    if (!productId) return;

    let cancelled = false;

    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await getSentimentSummary(productId);
        if (!cancelled) setSentiment(data);
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Failed to fetch sentiment data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetch();
    return () => { cancelled = true; };
  }, [productId]);

  return { sentiment, loading, error };
}
