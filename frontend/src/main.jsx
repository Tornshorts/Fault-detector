import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./app.css"; // optional: add your CSS here

function Dashboard() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch alerts from Flask API
  const fetchAlerts = async () => {
    try {
      const res = await fetch("/api/alerts");
      const data = await res.json();
      setAlerts(data.alerts || []);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching alerts:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts(); // initial load
    const interval = setInterval(fetchAlerts, 5000); // refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Determine row color based on status
  const getStatusColor = (status) => {
    if (!status) return "#fff";
    if (status.includes("OVER") || status.includes("WARNING")) return "#ffcccc"; // red for faults
    if (status.includes("HEALTHY")) return "#ccffcc"; // green for healthy
    if (status.includes("NIGHTTIME")) return "#e0e0e0"; // grey for night idle
    return "#fff"; // default white
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1 style={{ textAlign: "center", color: "#0c1929" }}>
        SolarGuard — Live Dashboard
      </h1>
      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 20 }}>
        <thead>
          <tr style={{ background: "#0c1929", color: "#fff" }}>
            <th>Panel ID</th>
            <th>Voltage (V)</th>
            <th>Current (mA)</th>
            <th>Load (%)</th>
            <th>Temp (°C)</th>
            <th>Status</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan="7">Loading...</td>
            </tr>
          ) : alerts.length === 0 ? (
            <tr>
              <td colSpan="7">No alerts found</td>
            </tr>
          ) : (
            alerts.map((alert, idx) => (
              <tr key={idx} style={{ background: getStatusColor(alert.status) }}>
                <td>{alert.panel_id}</td>
                <td>{alert.voltage}</td>
                <td>{alert.current}</td>
                <td>{alert.load}</td>
                <td>{alert.temperature}</td>
                <td>{alert.status}</td>
                <td>{new Date(alert.timestamp).toLocaleString()}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<Dashboard />);