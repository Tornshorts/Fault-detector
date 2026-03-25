import { List, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import './AlertsTable.css';

function getStatusClass(status) {
  if (!status) return 'healthy';
  const s = status.toUpperCase();
  if (s.includes('NIGHTTIME')) return 'night';
  if (s.includes('OVER') || s.includes('FAIL')) return 'fault';
  if (s.includes('LOW') || s.includes('HIGH')) return 'warning';
  return 'healthy';
}

function getStatusLabel(status) {
  const cls = getStatusClass(status);
  if (cls === 'night') return '🌙 ' + status;
  if (cls === 'fault') return '🚨 ' + status;
  if (cls === 'warning') return '⚠️ ' + status;
  return '✅ ' + status;
}

function formatTime(timestamp) {
  if (!timestamp) return '--';
  const d = new Date(timestamp);
  return d.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default function AlertsTable({ alerts }) {
  const [expanded, setExpanded] = useState(true);
  const [showCount, setShowCount] = useState(15);

  const visible = alerts.slice(0, showCount);
  const hasMore = alerts.length > showCount;

  return (
    <section className="alerts-table-section animate-fade-in" id="alerts-section">
      <div className="table-section-header" onClick={() => setExpanded(!expanded)}>
        <h2 className="section-title">
          <List size={20} />
          Recent Readings
          <span className="table-count">{alerts.length}</span>
        </h2>
        <button className="expand-toggle" aria-label="Toggle table">
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>

      {expanded && (
        <div className="table-card">
          <div className="table-wrapper">
            <table id="alerts-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Panel</th>
                  <th>Voltage (V)</th>
                  <th>Current (mA)</th>
                  <th>Load (%)</th>
                  <th>Temp (°C)</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      <div className="table-empty">
                        <span className="table-empty-icon">📡</span>
                        <p>Waiting for sensor data...</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  visible.map((a, i) => {
                    const cls = getStatusClass(a.status);
                    return (
                      <tr key={i} className={`row-${cls}`}>
                        <td className="td-time">{formatTime(a.timestamp)}</td>
                        <td className="td-panel">{a.panel_id || '--'}</td>
                        <td>{a.voltage?.toFixed(2) ?? '--'}</td>
                        <td>{a.current?.toFixed(0) ?? '--'}</td>
                        <td>{a.load?.toFixed(1) ?? '--'}</td>
                        <td>{a.temperature?.toFixed(1) ?? '--'}</td>
                        <td>
                          <span className={`badge badge-${cls}`}>
                            {a.status || 'UNKNOWN'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div className="table-load-more">
              <button onClick={() => setShowCount(s => s + 15)}>
                Show More ({alerts.length - showCount} remaining)
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
