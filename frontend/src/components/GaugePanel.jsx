import './GaugePanel.css';

function Gauge({ label, value, min, max, unit, color, thresholds = [] }) {
  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const rotation = -135 + (pct / 100) * 270; // 270° arc
  
  // Determine gauge color based on thresholds
  let activeColor = color;
  for (const t of thresholds) {
    if (t.type === 'above' && value > t.value) activeColor = t.color;
    if (t.type === 'below' && value < t.value) activeColor = t.color;
  }

  return (
    <div className="gauge">
      <svg viewBox="0 0 120 120" className="gauge-svg">
        {/* Background arc */}
        <circle
          cx="60" cy="60" r="50"
          fill="none"
          stroke="var(--gray-200)"
          strokeWidth="8"
          strokeDasharray="330 110"
          strokeDashoffset="-55"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <circle
          cx="60" cy="60" r="50"
          fill="none"
          stroke={activeColor}
          strokeWidth="8"
          strokeDasharray={`${pct * 3.3} ${330 - pct * 3.3 + 110}`}
          strokeDashoffset="-55"
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0 0 6px ${activeColor}40)`,
            transition: 'stroke-dasharray 0.8s ease, stroke 0.3s ease',
          }}
        />
        {/* Needle */}
        <line
          x1="60" y1="60"
          x2="60" y2="22"
          stroke={activeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          transform={`rotate(${rotation}, 60, 60)`}
          style={{ transition: 'transform 0.8s ease' }}
        />
        {/* Center dot */}
        <circle cx="60" cy="60" r="4" fill={activeColor} />
      </svg>
      <div className="gauge-info">
        <span className="gauge-value" style={{ color: activeColor }}>
          {value != null ? (typeof value === 'number' ? value.toFixed(1) : value) : '--'}
        </span>
        <span className="gauge-unit">{unit}</span>
      </div>
      <span className="gauge-label">{label}</span>
      <div className="gauge-range">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

export default function GaugePanel({ latest }) {
  const voltage = latest?.voltage ?? 0;
  const current = latest?.current ?? 0;
  const temperature = latest?.temperature ?? 0;
  const load = latest?.load ?? 0;

  return (
    <section className="gauge-panel animate-fade-in" id="gauge-section">
      <h2 className="section-title" style={{ marginBottom: '1.25rem' }}>
        ⚡ Real-Time Gauges
      </h2>
      <div className="gauge-grid">
        <Gauge
          label="Voltage"
          value={voltage}
          min={0} max={6}
          unit="V"
          color="#f97316"
          thresholds={[
            { type: 'above', value: 5.5, color: '#ef4444' },
            { type: 'below', value: 1.0, color: '#f59e0b' },
          ]}
        />
        <Gauge
          label="Current"
          value={current}
          min={0} max={1200}
          unit="mA"
          color="#3b82f6"
          thresholds={[
            { type: 'above', value: 1000, color: '#ef4444' },
          ]}
        />
        <Gauge
          label="Temperature"
          value={temperature}
          min={0} max={80}
          unit="°C"
          color="#10b981"
          thresholds={[
            { type: 'above', value: 60, color: '#ef4444' },
            { type: 'above', value: 45, color: '#f59e0b' },
          ]}
        />
        <Gauge
          label="Light / Load"
          value={load}
          min={0} max={100}
          unit="%"
          color="#8b5cf6"
          thresholds={[
            { type: 'below', value: 5, color: '#f59e0b' },
          ]}
        />
      </div>
    </section>
  );
}
