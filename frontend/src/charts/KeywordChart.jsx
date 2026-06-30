import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function KeywordChart({ positiveKeywords = [], negativeKeywords = [] }) {
  // Merge positive and negative keywords for comparison representation
  const getChartData = () => {
    const data = [];
    const maxLen = Math.max(positiveKeywords.length, negativeKeywords.length, 6);

    for (let i = 0; i < maxLen; i++) {
      const pos = positiveKeywords[i];
      const neg = negativeKeywords[i];
      if (pos || neg) {
        data.push({
          posWord: pos ? `${pos.word}` : "",
          posCount: pos ? pos.count : 0,
          negWord: neg ? `${neg.word}` : "",
          negCount: neg ? neg.count : 0,
        });
      }
    }
    return data.slice(0, 8); // top 8 entries
  };

  const chartData = getChartData();

  return (
    <div className="card grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Positive Keywords Bar */}
      <div>
        <h3 className="section-title mb-4 text-[#22c55e]">Top Positive Keywords</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 16, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis type="number" tick={{ fill: "#8892b0", fontSize: 11 }} axisLine={false} />
            <YAxis
              type="category"
              dataKey="posWord"
              tick={{ fill: "#8892b0", fontSize: 11 }}
              axisLine={false}
              width={64}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1c2333",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "0.75rem",
                color: "#e8eaf6",
              }}
            />
            <Bar dataKey="posCount" fill="#22c55e" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Negative Keywords Bar */}
      <div>
        <h3 className="section-title mb-4 text-[#ef4444]">Top Negative Keywords</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 16, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis type="number" tick={{ fill: "#8892b0", fontSize: 11 }} axisLine={false} />
            <YAxis
              type="category"
              dataKey="negWord"
              tick={{ fill: "#8892b0", fontSize: 11 }}
              axisLine={false}
              width={64}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1c2333",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "0.75rem",
                color: "#e8eaf6",
              }}
            />
            <Bar dataKey="negCount" fill="#ef4444" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
