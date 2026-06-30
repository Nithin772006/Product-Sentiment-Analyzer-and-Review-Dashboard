import { Link } from "react-router-dom";
import { FiArrowLeft } from "react-icons/fi";

export default function NotFound() {
  return (
    <div className="max-w-md mx-auto px-6 py-20 text-center flex flex-col items-center justify-center gap-4 flex-1">
      <span className="text-7xl">🔍</span>
      <h1 className="text-4xl font-extrabold text-[#e8eaf6] tracking-tight">404 - Page Not Found</h1>
      <p className="text-sm text-[#8892b0] leading-relaxed max-w-sm">
        The link you followed might be broken, or the page has been moved.
      </p>
      <Link to="/" className="btn-primary mt-4">
        <FiArrowLeft /> Back to Dashboard
      </Link>
    </div>
  );
}
