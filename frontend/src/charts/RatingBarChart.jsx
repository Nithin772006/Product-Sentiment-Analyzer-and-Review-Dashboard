/**
 * src/charts/RatingBarChart.jsx
 * ──────────────────────────────
 * Horizontal bar chart showing the star-rating distribution (1★ → 5★).
 *
 * Props:
 *   distribution - { "1": n, "2": n, "3": n, "4": n, "5": n }
 *
 * TODO Phase 2: Wire real data from useSentiment hook.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const STAR_COLORS = {
  '5': '#22c55e',
  '4': '#86efac',
  '3': '#f59e0b',
  '2': '#fb923c',
  '1': '#ef4444',
};

const PLACEHOLDER = [
  { star: '5★', count: 420 },
  { star: '4★', count: 280 },
  { star: '3★', count: 95  },
  { star: '2★', count: 42  },
  { star: '1★', count: 63  },
];

export default function RatingBarChart({ distribution }) {
  const chartData = distribution
    ? Object.entries(distribution)
        .sort(([a], [b]) => Number(b) - Number(a))
        .map(([star, count]) => ({ star: `${star}★`, count }))
    : PLACEHOLDER;

  return (
    <div className="card">
      <h3 className="section-title mb-4">Rating Distribution</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis type="number" tick={{ fill: '#8892b0', fontSize: 12 }} axisLine={false} />
          <YAxis
            type="category"
            dataKey="star"
            tick={{ fill: '#8892b0', fontSize: 12 }}
            axisLine={false}
            width={32}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            contentStyle={{
              backgroundColor: '#1c2333',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '0.75rem',
              color: '#e8eaf6',
            }}
          />
          <Bar dataKey="count" radius={[0, 6, 6, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.star} fill={STAR_COLORS[entry.star.charAt(0)] || '#3361ff'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
