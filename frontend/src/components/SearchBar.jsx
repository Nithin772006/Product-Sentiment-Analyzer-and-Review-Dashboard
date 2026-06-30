import { useState } from "react";
import { FiSearch } from "react-icons/fi";

export default function SearchBar({ onSearch, placeholder, isLoading }) {
  const [query, setQuery] = useState("");
  const [maxPages, setMaxPages] = useState(5);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), maxPages);
  };

  const isUrl = query.startsWith("http://") || query.startsWith("https://");

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl">
      <div className="flex flex-col md:flex-row gap-3 rounded-2xl border p-2 bg-[#161b27] border-[rgba(255,255,255,0.08)] shadow-lg">
        {/* Input Text Box */}
        <div className="relative flex-1 flex items-center">
          <FiSearch className="absolute left-4 text-xl text-[#8892b0]" />
          <input
            type="text"
            className="w-full bg-transparent pl-12 pr-4 py-3 text-sm text-[#e8eaf6] placeholder-[#8892b0] focus:outline-none"
            placeholder={placeholder || "Enter Amazon/Flipkart product link, or search keyword..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {/* Dynamic scraper depth control if URL is pasted */}
        {isUrl && (
          <div className="flex items-center gap-2 px-3 border-t md:border-t-0 md:border-l border-[rgba(255,255,255,0.08)]">
            <span className="text-xs text-[#8892b0] whitespace-nowrap">Pages to scrape:</span>
            <select
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
              className="bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-lg text-xs text-[#e8eaf6] py-1.5 px-2.5 focus:outline-none"
            >
              <option value={2}>2 pages</option>
              <option value={5}>5 pages</option>
              <option value={10}>10 pages</option>
              <option value={20}>20 pages</option>
            </select>
          </div>
        )}

        {/* Submit Search Button */}
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="btn-primary justify-center px-6 py-3 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Processing..." : isUrl ? "Import & Scrape" : "Search DB"}
        </button>
      </div>
      
      {isUrl && (
        <p className="mt-2 text-xs text-[#3361ff] text-center">
          🔗 Amazon/Flipkart link detected. We will trigger real-time scraping & sentiment extraction!
        </p>
      )}
    </form>
  );
}
