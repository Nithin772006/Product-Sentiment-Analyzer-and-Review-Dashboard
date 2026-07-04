import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { FiArrowLeft, FiSearch, FiFrown, FiBox } from "react-icons/fi";
import apiService from "../api/api";
import ProductCard from "../components/ProductCard";
import Loader from "../components/Loader";

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    async function executeSearch() {
      if (!query.trim()) {
        setProducts([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setErrorMsg("");

      try {
        const response = await apiService.searchProducts(query);
        setProducts(response.data || []);
      } catch (err) {
        console.error("Search query execution failed", err);
        setErrorMsg("Failed to complete search query. Ensure backend is running.");
      } finally {
        setIsLoading(false);
      }
    }

    executeSearch();
  }, [query]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-6">
      {/* Back button */}
      <div>
        <Link to="/" className="inline-flex items-center gap-1 text-xs text-[#8892b0] hover:text-[#3361ff]">
          <FiArrowLeft /> Back to Search
        </Link>
      </div>

      {/* Header section */}
      <div className="border-b border-[rgba(255,255,255,0.05)] pb-4 mb-2">
        <h1 className="page-title text-[#e8eaf6] flex items-center gap-2">
          <FiSearch className="text-[#3361ff]" /> Search Results
        </h1>
        <p className="text-xs text-[#8892b0] mt-1">
          Showing similar products from your database for: <span className="font-semibold text-[#e8eaf6]">"{query}"</span>
        </p>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-[#ef4444] rounded-xl text-xs">
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Grid listing */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <Loader />
          <h3 className="text-lg font-bold text-[#e8eaf6]">Searching Products...</h3>
          <p className="text-xs text-[#8892b0] max-w-md text-center">
            Checking saved products and ranking the closest database matches.
          </p>
        </div>
      ) : products.length === 0 ? (
        <div className="card text-center py-16 flex flex-col items-center justify-center gap-4">
          <FiFrown className="text-4xl text-[#8892b0]" />
          <h3 className="text-lg font-bold text-[#e8eaf6]">No Match Found</h3>
          <p className="text-xs text-[#8892b0] max-w-sm">
            We couldn't find any products in our database matching <span className="font-semibold">"{query}"</span>.
          </p>
          <div className="mt-3 max-w-md bg-[#161b27] border border-[rgba(255,255,255,0.05)] p-4 rounded-xl text-left">
            <span className="text-[10px] text-[#3361ff] font-semibold uppercase tracking-wider block mb-1">
              Want to scrape this product?
            </span>
            <p className="text-[11px] text-[#8892b0] leading-relaxed">
              Paste the exact <span className="font-semibold">Amazon</span> or <span className="font-semibold">Flipkart</span> product URL on the home page to import it directly.
            </p>
          </div>
          <Link to="/" className="btn-primary mt-4">
            Try a URL Import
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
