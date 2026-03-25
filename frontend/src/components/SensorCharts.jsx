import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart
} from 'recharts';
import { Zap, Thermometer, Sun, BarChart3 } from 'lucide-react';
import './SensorCharts.css';

const CHART_CONFIGS = [
  {
    key: 'voltage',
    label: 'Voltage',
    unit: 'V',
    color: '#f97316',
    gradientId: 'voltageGrad',
    icon: <Zap size={16} />,
    domain: [0, 6],
    thresholds: [
      { value: 5.5, label: 'Over', color: '#ef4444' },
      { value: 1.0, label: 'Low', color: '#f59e0b' },
    ],
  },
  {
    key: 'current',
    label: 'Current',
    unit: 'mA',
    color: '#3b82f6',
    gradientId: 'currentGrad',
    icon: <BarChart3 size={16} />,
    domain: [0, 'auto'],
    thresholds: [
      { value: 1000, label: 'Over', color: '#ef4444' },
    ],
  },
  {
    key: 'temperature',
    label: 'Temperature',
    unit: '°C',
    color: '#ef4444',
    gradientId: 'tempGrad',
    icon: <Thermometer size={16} />,
    domain: [0, 80],
    thresholds: [
      { value: 60, label: 'Critical', color: '#ef4444' },
      { value: 45, label: 'High', color: '#f59e0b' },
    ],
  },
  {
    key: 'load',
    label: 'Light / Load',
    unit: '%',
    color: '#10b981',
    gradientId: 'loadGrad',
    icon: <Sun size={16} />,
    domain: [0, 100],
    thresholds: [
      { value: 5, label: 'Low', color: '#f59e0b' },
    ],
  },
];

function CustomTooltip({ active, payload, label, config }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-time">{label}</p>
      <p className="chart-tooltip-value" style={{ color: config.color }}>
        {payload[0].value?.toFixed(2)} {config.unit}
      </p>
    </div>
  );
}

function SingleChart({ config, data }) {
  const latestVal = data.length > 0 ? data[data.length - 1][config.key] : null;

  return (
    <div className="chart-card animate-fade-in">
      <div className="chart-card-header">
        <div className="chart-card-title">
          <span className="chart-card-icon" style={{ color: config.color }}>
            {config.icon}
          </span>
          <h3>{config.label}</h3>
        </div>
        <div className="chart-card-live">
          <span className="chart-live-value" style={{ color: config.color }}>
            {latestVal != null ? latestVal.toFixed(config.key === 'current' ? 0 : 2) : '--'}
          </span>
          <span className="chart-live-unit">{config.unit}</span>
        </div>
      </div>

      <div className="chart-card-body">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id={config.gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={config.color} stopOpacity={0.3} />
                <stop offset="100%" stopColor={config.color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-200)" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: 'var(--gray-400)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--gray-200)' }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={config.domain}
              tick={{ fontSize: 11, fill: 'var(--gray-400)' }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip content={<CustomTooltip config={config} />} />

            {/* Threshold reference lines */}
            {config.thresholds.map(t => (
              <line key={t.label} />
            ))}

            <Area
              type="monotone"
              dataKey={config.key}
              stroke={config.color}
              strokeWidth={2.5}
              fill={`url(#${config.gradientId})`}
              dot={false}
              activeDot={{
                r: 5,
                fill: config.color,
                stroke: '#fff',
                strokeWidth: 2,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Threshold indicators */}
      <div className="chart-thresholds">
        {config.thresholds.map(t => (
          <span key={t.label} className="threshold-tag" style={{ color: t.color, borderColor: t.color }}>
            {t.label}: {t.value} {config.unit}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function SensorCharts({ timeSeries }) {
  const [visibleCharts, setVisibleCharts] = useState(
    CHART_CONFIGS.map(c => c.key)
  );

  const toggleChart = (key) => {
    setVisibleCharts(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };

  return (
    <section className="sensor-charts-section" id="charts-section">
      <div className="section-header">
        <h2 className="section-title">
          <BarChart3 size={20} />
          Live Sensor Data
        </h2>
        <div className="chart-toggles">
          {CHART_CONFIGS.map(c => (
            <button
              key={c.key}
              className={`chart-toggle ${visibleCharts.includes(c.key) ? 'active' : ''}`}
              onClick={() => toggleChart(c.key)}
              style={{ '--toggle-color': c.color }}
            >
              {c.icon}
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div className="charts-grid">
        {CHART_CONFIGS.filter(c => visibleCharts.includes(c.key)).map(config => (
          <SingleChart key={config.key} config={config} data={timeSeries} />
        ))}
      </div>

      {timeSeries.length === 0 && (
        <div className="charts-empty">
          <BarChart3 size={48} />
          <p>Waiting for sensor data to display charts...</p>
        </div>
      )}
    </section>
  );
}
