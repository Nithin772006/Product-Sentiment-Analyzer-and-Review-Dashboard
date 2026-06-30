import ReviewCard from "./ReviewCard";

export default function ReviewList({ reviews, sentiments, isLoading }) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        {[1, 2, 3].map((n) => (
          <div key={n} className="card animate-pulse flex flex-col gap-3 min-h-[140px]">
            <div className="flex justify-between items-center pb-3 border-b border-[rgba(255,255,255,0.05)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#161b27] rounded-full"></div>
                <div className="flex flex-col gap-1.5">
                  <div className="w-24 h-4 bg-[#161b27] rounded"></div>
                  <div className="w-16 h-3 bg-[#161b27] rounded"></div>
                </div>
              </div>
              <div className="w-20 h-6 bg-[#161b27] rounded-full"></div>
            </div>
            <div className="w-full h-4 bg-[#161b27] rounded mt-2"></div>
            <div className="w-3/4 h-4 bg-[#161b27] rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!reviews || reviews.length === 0) {
    return (
      <div className="card text-center py-12 flex flex-col items-center justify-center gap-3">
        <span className="text-4xl">💬</span>
        <h3 className="text-lg font-semibold text-[#e8eaf6]">No reviews found</h3>
        <p className="text-sm text-[#8892b0] max-w-md">
          There are no reviews matching the current filters or no reviews have been scraped yet.
        </p>
      </div>
    );
  }

  // Create a map of review_id -> sentiment for rapid O(1) lookup
  const sentimentsMap = {};
  if (sentiments) {
    sentiments.forEach((s) => {
      sentimentsMap[s.review_id] = s;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {reviews.map((review) => (
        <ReviewCard
          key={review.id}
          review={review}
          sentiment={sentimentsMap[review.id]}
        />
      ))}
    </div>
  );
}
