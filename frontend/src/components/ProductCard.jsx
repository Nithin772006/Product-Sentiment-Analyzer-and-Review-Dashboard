import { Link } from "react-router-dom";
import { FiArrowRight, FiActivity, FiTag, FiShoppingBag } from "react-icons/fi";

export default function ProductCard({ product }) {
  const brandName = product.brand || "Generic";
  const sourceName = product.source?.toLowerCase() === "amazon" ? "Amazon" : "Flipkart";

  const formattedDate = product.last_scraped
    ? new Date(product.last_scraped).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "Never Scraped";

  return (
    <div className="card flex flex-col justify-between h-full group hover:border-[#3361ff]/30 transition-all duration-300">
      <div>
        {/* Brand & Platform */}
        <div className="flex justify-between items-center mb-3">
          <span className="inline-flex items-center gap-1 text-[10px] uppercase font-semibold text-[#8892b0] bg-[#161b27] px-2.5 py-1 rounded-full">
            <FiTag className="text-xs" /> {brandName}
          </span>
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded ${
              sourceName === "Amazon"
                ? "bg-amber-500/10 text-amber-500"
                : "bg-blue-500/10 text-blue-500"
            }`}
          >
            {sourceName}
          </span>
        </div>

        {/* Product Title */}
        <h3 className="text-base font-bold text-[#e8eaf6] line-clamp-2 leading-snug group-hover:text-[#3361ff] transition-colors duration-200">
          {product.product_name}
        </h3>
        
        {product.price && (
          <div className="mt-2 inline-flex bg-[#161b27] px-2 py-1 rounded-md text-xs font-bold text-[#34d399] border border-[rgba(255,255,255,0.05)]">
            {product.price}
          </div>
        )}

        {/* Metrics Row */}
        <div className="grid grid-cols-2 gap-2 mt-4 bg-[#161b27] p-2.5 rounded-xl border border-[rgba(255,255,255,0.03)] text-center">
          <div>
            <span className="text-[10px] text-[#8892b0] uppercase">Rating</span>
            <div className="text-sm font-extrabold text-[#f59e0b] mt-0.5">
              ★ {product.average_rating?.toFixed(1) || "0.0"}
            </div>
          </div>
          <div>
            <span className="text-[10px] text-[#8892b0] uppercase">Reviews</span>
            <div className="text-sm font-extrabold text-[#e8eaf6] mt-0.5">
              {product.total_reviews || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Navigation */}
      <div className="border-t border-[rgba(255,255,255,0.05)] pt-3.5 mt-4 flex items-center justify-between">
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] text-[#8892b0] uppercase tracking-wider">Last Sync</span>
          <span className="text-xs font-medium text-[#e8eaf6]">{formattedDate}</span>
        </div>

        <Link
          to={`/products/${product.id}`}
          className="inline-flex items-center gap-1 text-sm font-semibold text-[#3361ff] hover:underline"
        >
          Analysis
          <FiArrowRight className="group-hover:translate-x-1 transition-transform duration-200" />
        </Link>
      </div>
    </div>
  );
}
