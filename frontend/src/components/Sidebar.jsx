import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  FiGrid,
  FiBox,
  FiFileText,
  FiSettings,
  FiHelpCircle,
  FiLogOut,
  FiActivity,
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
    { label: "Reports", to: "/reports", icon: <FiFileText /> },
    { label: "Settings", to: "/settings", icon: <FiSettings /> },
    { label: "About Engine", to: "/about", icon: <FiHelpCircle /> },
  ];

  return (
    <aside className="w-64 border-r border-[rgba(255,255,255,0.06)] bg-[#161b27] flex flex-col justify-between min-h-screen sticky top-0">
      {/* Brand logo header */}
      <div>
        <div className="flex items-center gap-3 px-6 py-6 border-b border-[rgba(255,255,255,0.05)]">
          <span className="text-3xl">🛍️</span>
          <div>
            <h1 className="text-base font-extrabold text-[#e8eaf6] tracking-tight">SentimentLens</h1>
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
                className={`flex items-center gap-3.5 px-4.5 py-3 rounded-xl text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? "bg-[#3361ff] text-white shadow-md shadow-[#3361ff]/15"
                    : "text-[#8892b0] hover:bg-[#1c2333] hover:text-[#e8eaf6]"
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer logout user section */}
      <div className="p-4 border-t border-[rgba(255,255,255,0.05)]">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3.5 w-full px-4.5 py-3 rounded-xl text-sm font-semibold text-[#ef4444] hover:bg-red-500/10 transition-all duration-150"
        >
          <FiLogOut className="text-lg" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
