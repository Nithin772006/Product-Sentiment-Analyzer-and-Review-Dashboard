import { Link } from "react-router-dom";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t bg-[#0f1117] border-[rgba(255,255,255,0.06)] mt-20">
      <div className="mx-auto max-w-7xl px-6 py-8 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo and Description */}
        <div className="text-center md:text-left">
          <Link to="/" className="flex items-center justify-center md:justify-start gap-2">
            <span className="text-xl">🛍️</span>
            <span className="text-sm font-extrabold text-[#e8eaf6]">SentimentLens</span>
          </Link>
          <p className="text-[11px] text-[#8892b0] mt-1.5 max-w-sm leading-relaxed">
            Real-time sentiment analyzer harvesting and dissecting reviews from Amazon & Flipkart.
          </p>
        </div>

        {/* Links & Copy */}
        <div className="flex flex-col items-center md:items-end gap-2 text-[11px] text-[#8892b0]">
          <div className="flex gap-4">
            <Link to="/" className="hover:text-[#3361ff]">Dashboard</Link>
            <Link to="/about" className="hover:text-[#3361ff]">About Engine</Link>
          </div>
          <p className="mt-1">
            © {currentYear} Cybernaut Internship Project. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
