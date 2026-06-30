import { FiFilter, FiRefreshCw } from "react-icons/fi";

export default function FilterPanel({ filters, onFilterChange, onReset }) {
  const handleChange = (key, value) => {
    onFilterChange(key, value);
  };

  return (
    <div className="card bg-[#161b27] flex flex-col gap-4 border-[rgba(255,255,255,0.06)] p-5">
      {/* Title Header */}
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.05)] pb-3">
        <div className="flex items-center gap-2 text-[#e8eaf6] font-semibold text-sm">
          <FiFilter className="text-[#3361ff]" />
          <span>Filter & Sort Reviews</span>
        </div>
        <button
          onClick={onReset}
          className="text-xs text-[#3361ff] hover:underline flex items-center gap-1 focus:outline-none"
        >
          <FiRefreshCw className="text-[10px]" /> Reset Filters
        </button>
      </div>

      {/* Grid Inputs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        {/* Sentiment Dropdown */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-[#8892b0] uppercase font-medium">Sentiment</span>
          <select
            value={filters.label || ""}
            onChange={(e) => handleChange("label", e.target.value || null)}
            className="bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl text-xs text-[#e8eaf6] py-2.5 px-3 focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
          >
            <option value="">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="negative">Negative</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>

        {/* Rating Dropdown */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-[#8892b0] uppercase font-medium">Rating</span>
          <select
            value={filters.rating || ""}
            onChange={(e) => handleChange("rating", e.target.value ? Number(e.target.value) : null)}
            className="bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl text-xs text-[#e8eaf6] py-2.5 px-3 focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
          >
            <option value="">All Ratings</option>
            <option value="5">★ 5 Stars</option>
            <option value="4">★ 4 Stars</option>
            <option value="3">★ 3 Stars</option>
            <option value="2">★ 2 Stars</option>
            <option value="1">★ 1 Star</option>
          </select>
        </div>

        {/* Source Dropdown */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-[#8892b0] uppercase font-medium">Platform</span>
          <select
            value={filters.source || ""}
            onChange={(e) => handleChange("source", e.target.value || null)}
            className="bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl text-xs text-[#e8eaf6] py-2.5 px-3 focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
          >
            <option value="">All Platforms</option>
            <option value="amazon">Amazon</option>
            <option value="flipkart">Flipkart</option>
          </select>
        </div>

        {/* Sorting Dropdown */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-[#8892b0] uppercase font-medium">Sort By</span>
          <select
            value={filters.sort_by || "review_date"}
            onChange={(e) => handleChange("sort_by", e.target.value)}
            className="bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl text-xs text-[#e8eaf6] py-2.5 px-3 focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
          >
            <option value="review_date">Review Date</option>
            <option value="rating">Star Rating</option>
            <option value="helpful_votes">Helpful Votes</option>
          </select>
        </div>

        {/* Order Dropdown */}
        <div className="flex flex-col gap-1 col-span-2 sm:col-span-1">
          <span className="text-[10px] text-[#8892b0] uppercase font-medium">Order</span>
          <select
            value={filters.order || "desc"}
            onChange={(e) => handleChange("order", e.target.value)}
            className="bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl text-xs text-[#e8eaf6] py-2.5 px-3 focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
          >
            <option value="desc">Newest / Highest</option>
            <option value="asc">Oldest / Lowest</option>
          </select>
        </div>
      </div>
    </div>
  );
}
