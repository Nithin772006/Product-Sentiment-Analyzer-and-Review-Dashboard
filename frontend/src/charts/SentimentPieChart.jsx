/**
 * src/charts/SentimentPieChart.jsx
 * ─────────────────────────────────
 * Donut-style pie chart showing positive / negative / neutral distribution.
 *
 * Props:
 *   data - { positive_count, negative_count, neutral_count }
 *
 * TODO Phase 2: Wire real data from useSentiment hook.
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const COLORS = {
  Positive: '#22c55e',
  Negative: '#ef4444',
  Neutral:  '#f59e0b',
};

const RADIAN = Math.PI / 180;
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={13} fontWeight={600}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export default function SentimentPieChart({ data }) {
  // Use placeholder data if none provided
  const chartData = data
    ? [
        { name: 'Positive', value: data.positive_count ?? 0 },
        { name: 'Negative', value: data.negative_count ?? 0 },
        { name: 'Neutral',  value: data.neutral_count  ?? 0 },
      ]
    : [
        { name: 'Positive', value: 60 },
        { name: 'Negative', value: 20 },
        { name: 'Neutral',  value: 20 },
      ];

  return (
    <div className="card">
      <h3 className="section-title mb-4">Sentiment Distribution</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={110}
            paddingAngle={3}
            dataKey="value"
            labelLine={false}
            label={renderCustomLabel}
          >
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={COLORS[entry.name]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1c2333',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '0.75rem',
              color: '#e8eaf6',
            }}
          />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: '13px', color: '#8892b0' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
