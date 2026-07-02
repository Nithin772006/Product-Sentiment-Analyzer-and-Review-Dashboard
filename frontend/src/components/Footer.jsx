import { Link } from "react-router-dom";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="mt-20 transition-colors duration-200"
      style={{
        borderTop: "1px solid var(--color-sidebar-border)",
        backgroundColor: "var(--color-bg-secondary)",
      }}
    >
      <div className="mx-auto max-w-7xl px-6 py-8 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo and Description */}
        <div className="text-center md:text-left">
          <Link to="/" className="flex items-center justify-center md:justify-start gap-2">
            <span className="text-xl">🛍️</span>
            <span
              className="text-sm font-extrabold"
              style={{ color: "var(--color-text-primary)" }}
            >
              SentimentLens
            </span>
          </Link>
          <p
            className="text-[11px] mt-1.5 max-w-sm leading-relaxed"
            style={{ color: "var(--color-text-muted)" }}
          >
            Real-time sentiment analyzer harvesting and dissecting reviews from Amazon &amp; Flipkart.
          </p>
        </div>

        {/* Links & Copy */}
        <div
          className="flex flex-col items-center md:items-end gap-2 text-[11px]"
          style={{ color: "var(--color-text-muted)" }}
        >
          <div className="flex gap-4">
            <Link to="/" className="hover:text-[#3361ff] transition-colors">Dashboard</Link>
            <Link to="/about" className="hover:text-[#3361ff] transition-colors">About Engine</Link>
          </div>
          <p className="mt-1">
            © {currentYear} Cybernaut Internship Project. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
