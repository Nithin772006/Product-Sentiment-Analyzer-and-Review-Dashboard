import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  FiBox,
  FiMessageSquare,
  FiSmile,
  FiFrown,
  FiMeh,
  FiClock,
} from "react-icons/fi";
import apiService from "../api/api";
import StatsCard from "../components/StatsCard";
import Loader from "../components/Loader";

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalReviews: 0,
    positiveReviews: 0,
    negativeReviews: 0,
    neutralReviews: 0,
  });
  const [recentProducts, setRecentProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        // Fetch only the 5 most recent products for the list
        const productsResponse = await apiService.getProducts(0, 5, "created_at", "desc");
        setRecentProducts(productsResponse.data || []);

        // Fetch pre-compiled aggregate dashboard numbers from the backend
        const summaryResponse = await apiService.getDashboardSummary();
        const summary = summaryResponse.data || {};

        setStats({
          totalProducts: summary.total_products || 0,
          totalReviews: summary.total_reviews || 0,
          positiveReviews: summary.sentiment_counts?.positive || 0,
          negativeReviews: summary.sentiment_counts?.negative || 0,
          neutralReviews: summary.sentiment_counts?.neutral || 0,
        });

      } catch (err) {
        console.error("Dashboard statistics load failed", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-6">
        <div className="w-48 h-8 bg-[#161b27] animate-pulse rounded-lg mb-4"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="card animate-pulse h-28 bg-[#1c2333] rounded-xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4">
          <div className="lg:col-span-2 card h-80 animate-pulse"></div>
          <div className="card h-80 animate-pulse"></div>
        </div>
      </div>
    );
  }

  const latestProduct = recentProducts[0];

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-8">
      {/* Header */}
      <div>
        <h1 className="page-title text-[#e8eaf6]">Dashboard Overview</h1>
        <p className="text-sm text-[#8892b0] mt-1">
          Compiled statistics across all tracked product scraping records and NLP sentiments.
        </p>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatsCard
          title="Total Products"
          value={stats.totalProducts}
          icon={<FiBox />}
          color="blue"
          description="Monitored items"
        />
        <StatsCard
          title="Total Reviews"
          value={stats.totalReviews}
          icon={<FiMessageSquare />}
          color="orange"
          description="Scraped in database"
        />
        <StatsCard
          title="Positive Sentiments"
          value={stats.positiveReviews}
          icon={<FiSmile className="text-[#22c55e]" />}
          color="green"
          trend="up"
          description="Classification positive"
        />
        <StatsCard
          title="Negative Sentiments"
          value={stats.negativeReviews}
          icon={<FiFrown className="text-[#ef4444]" />}
          color="red"
          trend="down"
          description="Classification negative"
        />
        <StatsCard
          title="Neutral Sentiments"
          value={stats.neutralReviews}
          icon={<FiMeh className="text-[#f59e0b]" />}
          color="orange"
          description="Classification neutral"
        />
      </div>

      {/* Grid: Recent Products Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Tracked Products List */}
        <div className="lg:col-span-2 card bg-[#161b27] border-[rgba(255,255,255,0.06)]">
          <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.05)] pb-4 mb-4">
            <h3 className="section-title text-[#e8eaf6] flex items-center gap-2">
              <FiClock className="text-[#3361ff]" /> Recent Activity
            </h3>
            <Link to="/" className="text-xs text-[#3361ff] hover:underline">
              Analyze New Product
            </Link>
          </div>

          {recentProducts.length === 0 ? (
            <div className="text-center py-12 text-[#8892b0]">
              No tracked items in the database.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {recentProducts.map((prod) => (
                <div
                  key={prod.id}
                  className="flex items-center justify-between p-3.5 bg-[#1c2333] hover:bg-[#212840] rounded-xl border border-[rgba(255,255,255,0.03)] transition-colors duration-200"
                >
                  <div className="flex flex-col gap-1 pr-4 min-w-0">
                    <span className="text-xs font-semibold text-[#e8eaf6] truncate">
                      {prod.product_name}
                    </span>
                    <span className="text-[10px] text-[#8892b0] uppercase">
                      {prod.brand || "Generic"} • {prod.source}
                    </span>
                  </div>

                  <Link
                    to={`/products/${prod.id}`}
                    className="btn-primary px-3 py-1.5 text-xs rounded-lg flex items-center"
                  >
                    View Analytics
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Latest Scraped Spotlight Panel */}
        <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] flex flex-col justify-between">
          <div>
            <h3 className="section-title text-[#e8eaf6] border-b border-[rgba(255,255,255,0.05)] pb-4 mb-4">
              Latest Spotlight
            </h3>
            {latestProduct ? (
              <div className="flex flex-col gap-3">
                <span className="text-xs text-[#3361ff] font-semibold uppercase tracking-wider">
                  Recently Scraped
                </span>
                <h4 className="text-sm font-bold text-[#e8eaf6] leading-snug line-clamp-3">
                  {latestProduct.product_name}
                </h4>
                <div className="mt-2 bg-[#1c2333] p-3 rounded-lg flex justify-between text-xs text-[#8892b0]">
                  <div>
                    Platform: <span className="font-semibold text-[#e8eaf6] capitalize">{latestProduct.source}</span>
                  </div>
                  <div>
                    Reviews: <span className="font-semibold text-[#e8eaf6]">{latestProduct.total_reviews}</span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-[#8892b0]">No products scraped yet.</p>
            )}
          </div>

          {latestProduct && (
            <Link
              to={`/products/${latestProduct.id}`}
              className="btn-primary w-full justify-center py-2.5 mt-6 rounded-xl"
            >
              Analyze Spotlight
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
