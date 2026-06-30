import { FiChevronLeft, FiChevronRight } from "react-icons/fi";

export default function Pagination({ page, total, limit, onPageChange }) {
  const totalPages = Math.ceil(total / limit) || 1;

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between border-t border-[rgba(255,255,255,0.05)] pt-4 mt-6">
      {/* Items count */}
      <span className="text-xs text-[#8892b0]">
        Showing page <span className="font-semibold text-[#e8eaf6]">{page}</span> of{" "}
        <span className="font-semibold text-[#e8eaf6]">{totalPages}</span> ({total} total items)
      </span>

      {/* Nav Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="p-2.5 rounded-xl bg-[#1c2333] border border-[rgba(255,255,255,0.08)] text-[#e8eaf6] hover:bg-[#212840] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150"
          aria-label="Previous Page"
        >
          <FiChevronLeft className="text-lg" />
        </button>
        <span className="text-xs font-semibold px-3 text-[#e8eaf6]">
          {page} / {totalPages}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="p-2.5 rounded-xl bg-[#1c2333] border border-[rgba(255,255,255,0.08)] text-[#e8eaf6] hover:bg-[#212840] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150"
          aria-label="Next Page"
        >
          <FiChevronRight className="text-lg" />
        </button>
      </div>
    </div>
  );
}
