import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function TrendChart({ reviews }) {
  // Extract and format chart points chronologically
  const getChartData = () => {
    if (!reviews || reviews.length === 0) {
      return [
        { date: "Jan", polarity: 0.1 },
        { date: "Feb", polarity: 0.2 },
        { date: "Mar", polarity: 0.15 },
        { date: "Apr", polarity: 0.4 },
        { date: "May", polarity: 0.6 },
      ];
    }

    // Map reviews to date & rating/polarity and sort chronologically
    const sorted = [...reviews]
      .filter((r) => r.review_date)
      .sort((a, b) => new Date(a.review_date) - new Date(b.review_date));

    // Aggregate by week or month to avoid line overcrowding
    const aggregated = {};
    sorted.forEach((r) => {
      const dateObj = new Date(r.review_date);
      const key = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, "0")}`; // YYYY-MM
      if (!aggregated[key]) {
        aggregated[key] = { totalRating: 0, count: 0 };
      }
      aggregated[key].totalRating += r.rating || 5;
      aggregated[key].count += 1;
    });

    const points = Object.entries(aggregated).map(([key, value]) => {
      const [year, month] = key.split("-");
      const dateLabel = new Date(year, month - 1).toLocaleString("default", {
        month: "short",
        year: "2-digit",
      });
      return {
        date: dateLabel,
        rating: round(value.totalRating / value.count, 2),
      };
    });

    return points.slice(-12); // keep last 12 months/weeks
  };

  const round = (val, dec) => Math.round(val * Math.pow(10, dec)) / Math.pow(10, dec);

  const chartData = getChartData();

  return (
    <div className="card">
      <h3 className="section-title mb-4">Rating Shift Over Time</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ left: -10, right: 10, top: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" tick={{ fill: "#8892b0", fontSize: 10 }} axisLine={false} />
          <YAxis
            type="number"
            domain={[1, 5]}
            tick={{ fill: "#8892b0", fontSize: 10 }}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1c2333",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "0.75rem",
              color: "#e8eaf6",
            }}
          />
          <Line
            type="monotone"
            dataKey="rating"
            stroke="#3361ff"
            strokeWidth={3}
            activeDot={{ r: 8 }}
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
