import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  FiGrid,
  FiBox,
  FiFileText,
  FiSettings,
  FiHelpCircle,
  FiLogOut,
  FiGlobe,
} from "react-icons/fi";

export default function Sidebar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("role");
    navigate("/login");
  };

  const navItems = [
    { label: "Home Hub", to: "/", icon: <FiBox /> },
    { label: "Dashboard", to: "/dashboard", icon: <FiGrid /> },
    { label: "Live Search", to: "/live-search", icon: <FiGlobe /> },
    { label: "Reports", to: "/reports", icon: <FiFileText /> },
    { label: "Settings", to: "/settings", icon: <FiSettings /> },
    { label: "About Engine", to: "/about", icon: <FiHelpCircle /> },
  ];

  return (
    <aside
      className="w-64 flex flex-col justify-between min-h-screen sticky top-0 transition-colors duration-200"
      style={{
        backgroundColor: "var(--color-bg-secondary)",
        borderRight: "1px solid var(--color-sidebar-border)",
      }}
    >
      {/* Brand logo header */}
      <div>
        <div
          className="flex items-center gap-3 px-6 py-6"
          style={{ borderBottom: "1px solid var(--color-divider)" }}
        >
          <span className="text-3xl">🛍️</span>
          <div>
            <h1
              className="text-base font-extrabold tracking-tight"
              style={{ color: "var(--color-text-primary)" }}
            >
              SentimentLens
            </h1>
            <span className="text-[10px] font-semibold text-[#3361ff] tracking-wider uppercase block">
              Analytics Studio
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex flex-col gap-1.5 px-4 py-6">
          {navItems.map((item) => {
            const isActive = pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? "bg-[#3361ff] text-white shadow-md shadow-[#3361ff]/15"
                    : ""
                }`}
                style={!isActive ? { color: "var(--color-text-muted)" } : {}}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor =
                      "var(--color-bg-card-hover)";
                    e.currentTarget.style.color = "var(--color-text-primary)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = "";
                    e.currentTarget.style.color = "var(--color-text-muted)";
                  }
                }}
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer logout user section */}
      <div
        className="p-4"
        style={{ borderTop: "1px solid var(--color-divider)" }}
      >
        <button
          onClick={handleLogout}
          className="flex items-center gap-3.5 w-full px-4 py-3 rounded-xl text-sm font-semibold text-[#ef4444] hover:bg-red-500/10 transition-all duration-150"
        >
          <FiLogOut className="text-lg" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
