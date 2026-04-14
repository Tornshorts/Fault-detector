# SolarGuard Fault Detection System

SolarGuard is a fault detection and monitoring system designed for solar panels. It collects real-time sensor data, evaluates panel health, identifies potential hardware faults or warnings, and presents everything on a modern React-based web dashboard.

## Project Structure

The project is divided into two main components:
- **`backend/`**: A Python Flask REST API that receives hardware sensor data, processes fault logic, and stores records in a SQLite database.
- **`frontend/`**: A React single-page application built with Vite, Recharts, and Lucide-React to visualize the incoming data in real-time.

## Features

- **Real-time Monitoring**: The dashboard polls the server every 3 seconds for the latest sensor readings.
- **Fault Logic Detection**: Evaluates incoming data (voltage, current, load percentage, temperature) to determine panel status (e.g., `HEALTHY`, `OVER_VOLTAGE`, `HIGH_TEMP`, `LOW_LOAD`).
- **Nighttime Mode**: Intelligently identifies nighttime conditions to avoid triggering false alarms for low voltage or load.
- **Data Visualization**: Includes stat grids, gauge panels, and time-series charts for insightful tracking.
- **Hardware Integration**: Can seamlessly parse plain text string-based or standard JSON sensor payloads typically sent from ESP IoT devices.

## Requirements

### Backend Requirements
- Python 3.8+
- Dependencies listed in `backend/requirements.txt`:
  - Flask (v3.1.2)
  - flask-cors (v5.0.1)
  - blinker, click, itsdangerous, Jinja2, MarkupSafe, Werkzeug

### Frontend Requirements
- Node.js (v18+)
- npm (Node Package Manager)

## Setup and Installation

### 1. Setting up the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment it is highly recommended:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask application:
   ```bash
   python run.py
   ```
   *The backend will automatically initialize the local SQLite database (`data/solar.db`) upon boot and will run on port `3000` (e.g., `http://localhost:3000`). Make sure this port is available.*

### 2. Setting up the Frontend

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the necessary NPM dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development frontend server:
   ```bash
   npm run dev
   ```
   *The Vite dev server should prompt a local port address in the terminal (usually `http://localhost:5173`) where the visualization dashboard is hosted.*

## How it Works

1. **Hardware Devices** (like an ESP8266 or ESP32) send POST requests to the backend endpoint (`/api/data`) containing real-time metrics such as Voltage, Current, Load percent, and Temperature.
2. The **Python Backend** receives this data, normalizes it, and routes it through the core `determine_status()` logic engine. 
   - Time-of-day logic ignores the naturally expected drops in voltage and load during twilight and nighttime.
   - Hard fault conditions (e.g., over-voltage, high-temperature, over-current) are tagged for immediate attention.
3. Once processed, the readings are saved to a local `solar.db` SQLite database.
4. The **React Frontend** dashboard continuously polls the `/api/alerts` GET endpoint. The payload flows into a custom `useAlerts` hook, enabling the charts, static gauges, real-time alert tables, and notification banners you see in the UI.

## License

This project is covered under the terms specified in the provided `LICENSE` file.
