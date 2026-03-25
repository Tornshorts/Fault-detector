import { Sun, Wifi, WifiOff } from 'lucide-react';
import './Navbar.css';

export default function Navbar({ connected, lastUpdated }) {
  return (
    <nav className="navbar" id="main-navbar">
      <div className="navbar-brand">
        <div className="navbar-logo">
          <Sun size={24} color="#fff" />
        </div>
        <h1 className="navbar-title">
          Solar<span>Guard</span>
        </h1>
      </div>

      <div className="navbar-right">
        <div className={`connection-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span>{connected ? 'Live' : 'Offline'}</span>
          <span className="status-dot" />
        </div>
        {lastUpdated && (
          <span className="last-updated">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>
    </nav>
  );
}
