import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiSearch, FiShoppingCart, FiStar, FiActivity } from "react-icons/fi";
import apiService from "../api/api";
import Loader from "../components/Loader";

export default function LiveSearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setErrorMsg("");
    setResults([]);

    try {
      const response = await apiService.searchAmazonLive(query.trim(), 12);
      setResults(response.data || []);
      if (response.data?.length === 0) {
        setErrorMsg("No products found on Amazon for that keyword.");
      }
    } catch (err) {
      console.error("Live search failed", err);
      setErrorMsg("Failed to fetch Amazon search results. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async (productUrl) => {
    setIsScraping(true);
    setErrorMsg("");
    try {
      // searchProducts with a URL triggers the scraper backend route
      const res = await apiService.searchProducts(productUrl);
      if (res.data && res.data.length > 0) {
        navigate(`/products/${res.data[0].id}`);
      } else {
        setErrorMsg("Failed to scrape the selected product.");
      }
    } catch (err) {
      console.error("Scraping failed", err);
      setErrorMsg("Error occurred while extracting reviews and analyzing sentiment.");
    } finally {
      setIsScraping(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-6">
      <div className="border-b border-[rgba(255,255,255,0.05)] pb-4 mb-2">
        <h1 className="page-title text-[#e8eaf6] flex items-center gap-2">
          <FiSearch className="text-[#3361ff]" /> Live Amazon Search
        </h1>
        <p className="text-xs text-[#8892b0] mt-1">
          Search Amazon directly and instantly analyze product sentiments.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-xl text-[#8892b0]" />
          <input
            type="text"
            className="w-full bg-[#161b27] border border-[rgba(255,255,255,0.08)] rounded-xl pl-12 pr-4 py-3 text-sm text-[#e8eaf6] placeholder-[#8892b0] focus:outline-none focus:ring-2 focus:ring-[#3361ff]/50"
            placeholder="E.g. OnePlus 12, Sony Headphones..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading || isScraping}
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading || isScraping}
          className="btn-primary px-6 py-3 disabled:opacity-50"
        >
          {isLoading ? "Searching..." : "Search Amazon"}
        </button>
      </form>

      {errorMsg && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-[#ef4444] rounded-xl text-sm font-medium">
          ⚠️ {errorMsg}
        </div>
      )}

      {isScraping && (
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <Loader />
          <h3 className="text-lg font-bold text-[#e8eaf6]">Extracting & Analyzing...</h3>
          <p className="text-xs text-[#8892b0]">This process scrapes the reviews and runs ML models. It might take 1-3 minutes.</p>
        </div>
      )}

      {!isScraping && results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-4">
          {results.map((product, idx) => (
            <div key={idx} className="card p-5 bg-[#1c2333] border border-[rgba(255,255,255,0.05)] rounded-2xl flex flex-col justify-between hover:-translate-y-1 transition-transform">
              <div className="flex gap-4 mb-4">
                <div className="w-20 h-20 bg-white rounded-xl overflow-hidden shrink-0 flex items-center justify-center p-1">
                  {product.thumbnail ? (
                    <img src={product.thumbnail} alt={product.product_name} className="max-w-full max-h-full object-contain mix-blend-multiply" />
                  ) : (
                    <FiShoppingCart className="text-2xl text-gray-300" />
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[#e8eaf6] line-clamp-3 leading-snug">
                    {product.product_name}
                  </h3>
                  {product.price && (
                    <div className="mt-2 inline-flex bg-[#161b27] px-2 py-1 rounded-md text-xs font-bold text-[#34d399] border border-[rgba(255,255,255,0.05)]">
                      {product.price}
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleAnalyze(product.product_url)}
                className="w-full btn-primary bg-[#3361ff] hover:bg-[#254bdb] py-2.5 flex items-center justify-center gap-2 mt-auto"
              >
                <FiActivity /> Analyze Sentiment
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
