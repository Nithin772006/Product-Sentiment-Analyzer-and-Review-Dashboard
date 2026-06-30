/**
 * src/components/Navbar.jsx
 * ──────────────────────────
 * Top navigation bar.
 * Phase 2: Add active link highlighting and mobile hamburger menu.
 */

import { Link, useLocation } from 'react-router-dom';

const NAV_LINKS = [
  { label: 'Home Hub',    to: '/' },
  { label: 'Dashboard',   to: '/dashboard' },
  { label: 'About Engine', to: '/about' },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="sticky top-0 z-50 border-b" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg-secondary)' }}>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl">🛍️</span>
          <span className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>
            SentimentLens
          </span>
        </Link>

        {/* Nav Links */}
        <ul className="flex items-center gap-1">
          {NAV_LINKS.map(({ label, to }) => {
            const isActive = pathname === to;
            return (
              <li key={to}>
                <Link
                  to={to}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors duration-150 ${
                    isActive
                      ? 'text-white'
                      : 'hover:text-white'
                  }`}
                  style={{
                    backgroundColor: isActive ? 'var(--color-accent-blue)' : 'transparent',
                    color: isActive ? '#fff' : 'var(--color-text-muted)',
                  }}
                >
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
