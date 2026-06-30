import { FiTrendingUp, FiTrendingDown, FiMinus } from "react-icons/fi";

export default function StatsCard({ title, value, icon, description, trend, color }) {
  const getTrendIcon = () => {
    if (trend === "up") return <FiTrendingUp className="text-xs text-[#22c55e]" />;
    if (trend === "down") return <FiTrendingDown className="text-xs text-[#ef4444]" />;
    return <FiMinus className="text-xs text-[#f59e0b]" />;
  };

  const getBorderColor = () => {
    if (color === "blue") return "hover:border-[#3361ff]/30";
    if (color === "green") return "hover:border-[#22c55e]/30";
    if (color === "red") return "hover:border-[#ef4444]/30";
    if (color === "orange") return "hover:border-[#f59e0b]/30";
    return "hover:border-[rgba(255,255,255,0.15)]";
  };

  return (
    <div className={`card ${getBorderColor()} group transition-all duration-300`}>
      <div className="flex justify-between items-start">
        {/* Value and Label */}
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#8892b0] block">
            {title}
          </span>
          <h2 className="text-3xl font-extrabold text-[#e8eaf6] mt-2 tracking-tight group-hover:scale-[1.02] origin-left transition-transform duration-200">
            {value}
          </h2>
        </div>

        {/* Icon wrapper */}
        <div className="bg-[#161b27] p-3.5 rounded-xl border border-[rgba(255,255,255,0.05)] text-xl text-[#3361ff] group-hover:bg-[#3361ff]/10 group-hover:text-[#3361ff] transition-all duration-200">
          {icon}
        </div>
      </div>

      {/* Description & Subtext */}
      {(description || trend) && (
        <div className="flex items-center gap-2 mt-4 text-xs text-[#8892b0] border-t border-[rgba(255,255,255,0.05)] pt-3">
          {trend && (
            <span className="flex items-center gap-0.5 font-medium">
              {getTrendIcon()}
            </span>
          )}
          <span>{description}</span>
        </div>
      )}
    </div>
  );
}
