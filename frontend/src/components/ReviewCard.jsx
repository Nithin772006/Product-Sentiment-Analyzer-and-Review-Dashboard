import { useState } from "react";
import { FiCheckCircle, FiThumbsUp, FiBarChart2, FiCalendar, FiUser } from "react-icons/fi";
import SentimentBadge from "./SentimentBadge";

export default function ReviewCard({ review, sentiment }) {
  const [showMetrics, setShowMetrics] = useState(false);

  const formattedDate = review.review_date
    ? new Date(review.review_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "Unknown Date";

  return (
    <div className="card flex flex-col gap-3">
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[rgba(255,255,255,0.05)] pb-3">
        <div className="flex items-center gap-3">
          <div className="bg-[#161b27] p-2 rounded-full text-[#8892b0]">
            <FiUser className="text-lg" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#e8eaf6]">{review.reviewer || "Anonymous"}</h4>
            <div className="flex items-center gap-1.5 mt-0.5 text-xs text-[#8892b0]">
              <FiCalendar className="text-xs" />
              <span>{formattedDate}</span>
              {review.source && (
                <>
                  <span>•</span>
                  <span className="capitalize">{review.source}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Sentiment Badge and Stars */}
        <div className="flex items-center gap-2">
          {sentiment && <SentimentBadge sentiment={sentiment.sentiment} />}
          <div className="flex items-center bg-[#161b27] px-2.5 py-1 rounded-lg">
            <span className="text-xs font-semibold text-[#f59e0b]">★ {review.rating?.toFixed(1) || "5.0"}</span>
          </div>
        </div>
      </div>

      {/* Review text */}
      <p className="text-sm text-[#8892b0] leading-relaxed break-words whitespace-pre-line">
        {review.review_text}
      </p>

      {/* Footer Details */}
      <div className="flex flex-wrap items-center justify-between gap-3 mt-2 border-t border-[rgba(255,255,255,0.05)] pt-3 text-xs">
        <div className="flex items-center gap-3">
          {review.verified_purchase && (
            <span className="inline-flex items-center gap-1 text-[#22c55e]">
              <FiCheckCircle className="text-xs" /> Verified Purchase
            </span>
          )}
          {review.helpful_votes > 0 && (
            <span className="inline-flex items-center gap-1 text-[#8892b0]">
              <FiThumbsUp /> {review.helpful_votes} helpful votes
            </span>
          )}
        </div>

        {/* Toggle Detailed NLP Metrics */}
        {sentiment && (
          <button
            onClick={() => setShowMetrics(!showMetrics)}
            className="inline-flex items-center gap-1 text-[#3361ff] hover:underline"
          >
            <FiBarChart2 />
            {showMetrics ? "Hide NLP Scores" : "Show NLP Scores"}
          </button>
        )}
      </div>

      {/* Sentiment Metrics Expandable Panel */}
      {showMetrics && sentiment && (
        <div className="mt-2 bg-[#161b27] p-3.5 rounded-xl border border-[rgba(255,255,255,0.05)] grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
          <div>
            <div className="text-[10px] text-[#8892b0] uppercase">Confidence</div>
            <div className="text-sm font-semibold text-[#e8eaf6] mt-0.5">
              {(sentiment.confidence * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-[#8892b0] uppercase">TextBlob Polarity</div>
            <div className="text-sm font-semibold text-[#e8eaf6] mt-0.5">
              {sentiment.polarity?.toFixed(3) || "0.000"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-[#8892b0] uppercase">Subjectivity</div>
            <div className="text-sm font-semibold text-[#e8eaf6] mt-0.5">
              {sentiment.subjectivity?.toFixed(3) || "0.000"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-[#8892b0] uppercase">VADER Compound</div>
            <div className="text-sm font-semibold text-[#e8eaf6] mt-0.5">
              {sentiment.vader_compound?.toFixed(3) || "0.000"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
