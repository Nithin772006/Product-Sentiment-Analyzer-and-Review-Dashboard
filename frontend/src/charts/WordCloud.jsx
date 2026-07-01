import { useState } from "react";
import { FiImage, FiAlertCircle } from "react-icons/fi";

export default function WordCloud({ productId }) {
  const [activeTab, setActiveTab] = useState("positive");
  const [imgError, setImgError] = useState(false);

  // Serve image from backend static files, not the /api route prefix.
  const backendBaseUrl = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/api\/?$/, "");
  const imageUrl = `${backendBaseUrl}/static/wordclouds/${activeTab}_${productId}.png?t=${Date.now()}`; // append timestamp to bypass browser caching

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setImgError(false);
  };

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.05)] pb-3">
        <h3 className="section-title flex items-center gap-2">
          <FiImage className="text-[#3361ff]" /> Sentiment Word Clouds
        </h3>

        {/* Tab Controls */}
        <div className="flex items-center gap-1.5 bg-[#161b27] p-1 rounded-xl">
          {["positive", "neutral", "negative"].map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabChange(tab)}
              className={`capitalize px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                activeTab === tab
                  ? tab === "positive"
                    ? "bg-[#22c55e] text-white"
                    : tab === "negative"
                    ? "bg-[#ef4444] text-white"
                    : "bg-[#f59e0b] text-white"
                  : "text-[#8892b0] hover:text-[#e8eaf6]"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Word Cloud Viewer Container */}
      <div className="bg-[#161b27] min-h-[220px] rounded-xl flex items-center justify-center border border-[rgba(255,255,255,0.03)] overflow-hidden p-4">
        {imgError ? (
          <div className="text-center flex flex-col items-center gap-2 max-w-xs py-8">
            <FiAlertCircle className="text-2xl text-[#8892b0]" />
            <h4 className="text-sm font-semibold text-[#e8eaf6]">No Word Cloud Generated</h4>
            <p className="text-[11px] text-[#8892b0] leading-relaxed">
              We need more review records categorized as <span className="font-semibold">{activeTab}</span> to render this word cloud.
            </p>
          </div>
        ) : (
          <img
            src={imageUrl}
            alt={`${activeTab} word cloud`}
            onError={() => setImgError(true)}
            className="max-h-[260px] max-w-full rounded-lg object-contain transition-all duration-300 hover:scale-[1.01]"
          />
        )}
      </div>
    </div>
  );
}
