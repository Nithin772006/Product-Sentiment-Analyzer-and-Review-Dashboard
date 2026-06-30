import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FiSearch, FiTrendingUp, FiShoppingBag, FiActivity } from "react-icons/fi";
import apiService from "../api/api";
import SearchBar from "../components/SearchBar";
import ProductCard from "../components/ProductCard";
import Loader from "../components/Loader";

export default function Home() {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch recent products
    apiService
      .getProducts(0, 6, "created_at", "desc")
      .then((res) => {
        setProducts(res.data || []);
      })
      .catch((err) => {
        console.error("Error loading home products", err);
        setErrorMsg("Could not fetch recent products. Ensure backend is running.");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const handleSearchOrScrape = async (query, maxPages) => {
    const isUrl = query.startsWith("http://") || query.startsWith("https://");
    
    if (isUrl) {
      // Paste URL triggers scraper directly
      setIsSearching(true);
      setErrorMsg("");
      try {
        const response = await apiService.searchAndScrapeProduct(query, maxPages);
        const productId = response.data.id;
        navigate(`/products/${productId}`);
      } catch (err) {
        console.error("Scraper import failure", err);
        setErrorMsg(err.message || "Failed to trigger scraper. Double check the product URL.");
      } finally {
        setIsSearching(false);
      }
    } else {
      // Direct text search redirects to search results page
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between">
      {/* Hero header section */}
      <section className="relative px-6 py-20 md:py-28 flex flex-col items-center text-center bg-gradient-to-b from-[#161b27] via-[#0f1117] to-[#0f1117]">
        {/* Decorative ambient light */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-[#3361ff]/15 rounded-full blur-[80px] pointer-events-none"></div>

        <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold text-[#3361ff] bg-[#3361ff]/10 border border-[#3361ff]/20 uppercase tracking-wider mb-6 animate-pulse">
          <FiActivity /> Live Review Sentiment Extractor
        </span>

        <h1 className="text-4xl md:text-6xl font-extrabold text-[#e8eaf6] tracking-tight max-w-4xl leading-tight">
          Unlock Product Insights with <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#3361ff] to-[#60a5fa]">Dual-Engine NLP</span>
        </h1>

        <p className="text-base md:text-lg text-[#8892b0] mt-6 max-w-2xl leading-relaxed">
          Paste an Amazon or Flipkart product URL to trigger our real-time scraper, clean raw reviews, 
          and run VADER + TextBlob sentiment classification.
        </p>

        {/* Centralized Search Bar */}
        <div className="mt-10 w-full flex justify-center z-10">
          <SearchBar onSearch={handleSearchOrScrape} isLoading={isSearching} />
        </div>

        {errorMsg && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 text-[#ef4444] rounded-xl text-xs max-w-lg">
            ⚠️ {errorMsg}
          </div>
        )}
      </section>

      {/* Grid listing section */}
      <section className="max-w-7xl mx-auto px-6 py-12 w-full">
        <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.05)] pb-4 mb-8">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <FiShoppingBag className="text-[#3361ff]" /> Recently Tracked Products
          </h2>
          <span className="text-xs text-[#8892b0]">{products.length} products listed</span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="card animate-pulse h-48 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <div className="w-16 h-4 bg-[#161b27] rounded"></div>
                    <div className="w-12 h-4 bg-[#161b27] rounded"></div>
                  </div>
                  <div className="w-full h-6 bg-[#161b27] rounded"></div>
                  <div className="w-2/3 h-4 bg-[#161b27] rounded mt-2"></div>
                </div>
                <div className="w-full h-8 bg-[#161b27] rounded"></div>
              </div>
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="card text-center py-16 flex flex-col items-center gap-3">
            <span className="text-5xl">📦</span>
            <h3 className="text-lg font-semibold text-[#e8eaf6]">No tracked products yet</h3>
            <p className="text-xs text-[#8892b0] max-w-md">
              Start by pasting a product URL from Amazon or Flipkart in the box above to scrape, analyze, and build a visual review dashboard.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
