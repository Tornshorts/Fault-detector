import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = import.meta.env.MODE === 'production'
  ? 'https://fault-detector-4mqx.onrender.com/api'
  : '/api';

export function useAlerts(pollInterval = 3000) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setAlerts(json.alerts || []);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    intervalRef.current = setInterval(fetchAlerts, pollInterval);
    return () => clearInterval(intervalRef.current);
  }, [fetchAlerts, pollInterval]);

  // Derived statistics
  const stats = (() => {
    if (!alerts.length) return { total: 0, healthy: 0, warnings: 0, faults: 0, nighttime: 0 };
    let healthy = 0, warnings = 0, faults = 0, nighttime = 0;
    alerts.forEach(a => {
      const s = (a.status || '').toUpperCase();
      if (s.includes('NIGHTTIME')) nighttime++;
      else if (s.includes('OVER') || s.includes('FAIL')) faults++;
      else if (s.includes('LOW') || s.includes('HIGH')) warnings++;
      else healthy++;
    });
    return { total: alerts.length, healthy, warnings, faults, nighttime };
  })();

  const latest = alerts.length > 0 ? alerts[0] : null;

  // Time-series data for charts (most recent 30, reversed so oldest first)
  const timeSeries = [...alerts].slice(0, 30).reverse().map((a, i) => {
    const ts = a.timestamp ? new Date(a.timestamp) : null;
    const timeLabel = ts
      ? ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : `#${i + 1}`;
    return {
      time: timeLabel,
      voltage: a.voltage ?? 0,
      current: a.current ?? 0,
      load: a.load ?? 0,
      temperature: a.temperature ?? 0,
      status: a.status || 'UNKNOWN',
    };
  });

  return { alerts, loading, error, stats, latest, timeSeries, lastUpdated, refetch: fetchAlerts };
}
