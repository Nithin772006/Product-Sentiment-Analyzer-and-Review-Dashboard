import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { FiArrowLeft, FiShoppingBag, FiStar, FiGrid, FiActivity } from "react-icons/fi";
import apiService from "../api/api";
import Loader from "../components/Loader";
import SentimentPie from "../charts/SentimentPie";
import RatingBar from "../charts/RatingBar";
import TrendChart from "../charts/TrendChart";
import KeywordChart from "../charts/KeywordChart";
import WordCloud from "../charts/WordCloud";
import FilterPanel from "../components/FilterPanel";
import ReviewList from "../components/ReviewList";
import Pagination from "../components/Pagination";

export default function ProductPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [sentiments, setSentiments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isReviewsLoading, setIsReviewsLoading] = useState(true);

  // Pagination & Filtering state
  const [page, setPage] = useState(1);
  const [totalReviews, setTotalReviews] = useState(0);
  const limit = 8;
  const [filters, setFilters] = useState({
    label: null,
    rating: null,
    source: null,
    sort_by: "review_date",
    order: "desc",
  });

  // Load product metadata & analytics
  useEffect(() => {
    async function loadProduct() {
      setIsLoading(true);
      try {
        const prodRes = await apiService.getProduct(id);
        setProduct(prodRes.data);

        const analyticsRes = await apiService.getProductAnalytics(id);
        setAnalytics(analyticsRes.data);
      } catch (err) {
        console.error("Failed to load product page details", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadProduct();
  }, [id]);

  // Load reviews list when filters or page changes
  useEffect(() => {
    async function loadReviews() {
      setIsReviewsLoading(true);
      try {
        const skip = (page - 1) * limit;
        const params = {
          skip,
          limit,
          rating: filters.rating,
          source: filters.source,
          sort_by: filters.sort_by,
          order: filters.order,
        };
        // If sentiment label is selected, backend supports label query parameter
        if (filters.label) {
          params.sentiment = filters.label;
        }

        const reviewsRes = await apiService.getProductReviews(id, params);
        setReviews(reviewsRes.data || []);
        setTotalReviews(reviewsRes.total || 0);

        // Fetch corresponding sentiments in batch
        const sentimentsRes = await apiService.getProductSentiments(id, {
          skip,
          limit,
          label: filters.label,
        });
        setSentiments(sentimentsRes.data || []);
      } catch (err) {
        console.error("Failed to load product reviews", err);
      } finally {
        setIsReviewsLoading(false);
      }
    }

    if (product) {
      loadReviews();
    }
  }, [id, page, filters, product]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1); // reset to first page
  };

  const handleResetFilters = () => {
    setFilters({
      label: null,
      rating: null,
      source: null,
      sort_by: "review_date",
      order: "desc",
    });
    setPage(1);
  };

  if (isLoading) {
    return <Loader fullPage message="Compiling product dashboard insights..." />;
  }

  if (!product) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-16 text-center flex flex-col items-center gap-4">
        <span className="text-5xl">⚠️</span>
        <h2 className="text-xl font-bold text-[#e8eaf6]">Product Not Found</h2>
        <p className="text-sm text-[#8892b0] max-w-sm">
          The product link might be broken or the record was deleted.
        </p>
        <Link to="/" className="btn-primary mt-2">
          <FiArrowLeft /> Back to Search
        </Link>
      </div>
    );
  }

  const summary = analytics?.sentiment_summary || {};
  const distribution = analytics?.rating_distribution || {};

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 w-full flex-1 flex flex-col gap-6">
      {/* Back breadcrumb */}
      <div>
        <Link to="/" className="inline-flex items-center gap-1 text-xs text-[#8892b0] hover:text-[#3361ff]">
          <FiArrowLeft /> Back to Hub
        </Link>
      </div>

      {/* Product Banner Section */}
      <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] flex flex-col md:flex-row justify-between items-start md:items-center gap-4 p-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="capitalize text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              {product.source}
            </span>
            <span className="text-xs text-[#8892b0] font-medium">{product.brand || "Generic"}</span>
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-[#e8eaf6] tracking-tight leading-snug">
            {product.product_name}
          </h1>
        </div>

        {/* Rating Metrics box */}
        <div className="flex items-center gap-4 bg-[#1c2333] border border-[rgba(255,255,255,0.04)] px-5 py-3 rounded-2xl">
          <div className="text-center">
            <span className="text-[10px] text-[#8892b0] uppercase">Rating</span>
            <div className="text-lg font-black text-[#f59e0b] mt-0.5 flex items-center gap-0.5">
              <FiStar className="fill-current" /> {product.average_rating?.toFixed(1) || "0.0"}
            </div>
          </div>
          <div className="w-[1px] h-8 bg-[rgba(255,255,255,0.08)]"></div>
          <div className="text-center">
            <span className="text-[10px] text-[#8892b0] uppercase">Reviews</span>
            <div className="text-lg font-black text-[#e8eaf6] mt-0.5">{product.total_reviews || 0}</div>
          </div>
        </div>
      </div>

      {/* Grid: Charts distributions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SentimentPie data={summary} />
        <RatingBar distribution={distribution} />
      </div>

      {/* Grid: Trend shift and Word Cloud generator */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TrendChart reviews={reviews} />
        <WordCloud productId={product.id} />
      </div>

      {/* Bar: Top keywords comparisons */}
      {analytics?.keywords && (
        <KeywordChart
          positiveKeywords={analytics.keywords.positive}
          negativeKeywords={analytics.keywords.negative}
        />
      )}

      {/* Filter and Reviews display */}
      <div className="flex flex-col gap-6 mt-4">
        <div className="border-b border-[rgba(255,255,255,0.05)] pb-3">
          <h2 className="text-lg font-bold flex items-center gap-2 text-[#e8eaf6]">
            <FiActivity className="text-[#3361ff]" /> Reviews Feed
          </h2>
        </div>

        {/* Filters dropdowns */}
        <FilterPanel filters={filters} onFilterChange={handleFilterChange} onReset={handleResetFilters} />

        {/* Reviews Cards List */}
        <ReviewList reviews={reviews} sentiments={sentiments} isLoading={isReviewsLoading} />

        {/* Pagination controls */}
        <Pagination page={page} total={totalReviews} limit={limit} onPageChange={(p) => setPage(p)} />
      </div>
    </div>
  );
}
