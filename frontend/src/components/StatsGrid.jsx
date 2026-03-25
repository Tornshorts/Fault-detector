import { Zap, Thermometer, Activity, Sun, Moon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import './StatsGrid.css';

function getStatusClass(status) {
  if (!status) return 'healthy';
  const s = status.toUpperCase();
  if (s.includes('NIGHTTIME')) return 'night';
  if (s.includes('OVER') || s.includes('FAIL')) return 'fault';
  if (s.includes('LOW') || s.includes('HIGH')) return 'warning';
  return 'healthy';
}

function StatCard({ icon, label, value, suffix, accentColor, trend }) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  return (
    <div className="stat-card animate-fade-in" style={{ '--accent': accentColor }}>
      <div className="stat-icon-wrapper">
        {icon}
      </div>
      <div className="stat-content">
        <span className="stat-label">{label}</span>
        <div className="stat-value-row">
          <span className="stat-value">{value}</span>
          {suffix && <span className="stat-suffix">{suffix}</span>}
        </div>
      </div>
      {trend && (
        <div className={`stat-trend ${trend}`}>
          <TrendIcon size={14} />
        </div>
      )}
    </div>
  );
}

export default function StatsGrid({ stats, latest }) {
  const statusCls = latest ? getStatusClass(latest.status) : 'healthy';

  return (
    <div className="stats-grid" id="stats-grid">
      <StatCard
        icon={<Activity size={20} />}
        label="Total Readings"
        value={stats.total}
        accentColor="var(--navy-500)"
      />
      <StatCard
        icon={<Zap size={20} />}
        label="Voltage"
        value={latest?.voltage?.toFixed(2) ?? '--'}
        suffix="V"
        accentColor="var(--orange-500)"
      />
      <StatCard
        icon={<Sun size={20} />}
        label="Current"
        value={latest?.current?.toFixed(0) ?? '--'}
        suffix="mA"
        accentColor="var(--solar-yellow)"
      />
      <StatCard
        icon={<Thermometer size={20} />}
        label="Temperature"
        value={latest?.temperature?.toFixed(1) ?? '--'}
        suffix="°C"
        accentColor={
          (latest?.temperature ?? 0) > 45 ? 'var(--red-500)' :
          (latest?.temperature ?? 0) > 35 ? 'var(--yellow-500)' : 'var(--green-500)'
        }
      />
      <div className={`stat-card stat-card--status stat-card--${statusCls} animate-fade-in`}>
        <div className="status-indicator-large">
          {statusCls === 'night' ? (
            <Moon size={22} className="night-icon" />
          ) : (
            <span className={`status-pulse ${statusCls}`} />
          )}
        </div>
        <div className="stat-content">
          <span className="stat-label">System Status</span>
          <span className={`stat-value stat-value--status ${statusCls}`}>
            {statusCls === 'healthy' ? 'Healthy'
              : statusCls === 'night' ? 'Night Mode'
              : statusCls === 'warning' ? 'Warning'
              : 'Fault'}
          </span>
          {statusCls === 'night' && (
            <span className="status-hint">Solar panel idle — no sunlight</span>
          )}
        </div>
      </div>
    </div>
  );
}
