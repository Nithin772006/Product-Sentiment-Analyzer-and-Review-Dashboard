import { FiSmile, FiFrown, FiMeh } from "react-icons/fi";

export default function SentimentBadge({ sentiment }) {
  const label = sentiment?.toLowerCase() || "neutral";

  if (label === "positive") {
    return (
      <span className="badge-positive inline-flex items-center gap-1">
        <FiSmile className="text-sm" />
        Positive
      </span>
    );
  }

  if (label === "negative") {
    return (
      <span className="badge-negative inline-flex items-center gap-1">
        <FiFrown className="text-sm" />
        Negative
      </span>
    );
  }

  return (
    <span className="badge-neutral inline-flex items-center gap-1">
      <FiMeh className="text-sm" />
      Neutral
    </span>
  );
}
