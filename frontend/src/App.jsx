import { useAlerts } from './hooks/useAlerts';
import Navbar from './components/Navbar';
import StatsGrid from './components/StatsGrid';
import GaugePanel from './components/GaugePanel';
import SensorCharts from './components/SensorCharts';
import AlertsTable from './components/AlertsTable';
import './App.css';

export default function App() {
  const { alerts, loading, error, stats, latest, timeSeries, lastUpdated } = useAlerts(3000);
  const connected = !error && !loading;

  return (
    <>
      <Navbar connected={connected} lastUpdated={lastUpdated} />

      <main className="main-container">
        {/* Error Banner */}
        {error && (
          <div className="error-banner animate-fade-in">
            <span>⚠️</span>
            <p>Cannot reach server: {error}. Retrying...</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="loading-state">
            <div className="loading-spinner" />
            <p>Connecting to SolarGuard...</p>
          </div>
        )}

        {!loading && (
          <>
            <StatsGrid stats={stats} latest={latest} />
            <GaugePanel latest={latest} />
            <SensorCharts timeSeries={timeSeries} />
            <AlertsTable alerts={alerts} />
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>SolarGuard Fault Detection System • Built with ❤️ for renewable energy</p>
      </footer>
    </>
  );
}
