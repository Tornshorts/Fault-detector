import re
import json
from flask import request, jsonify, Blueprint
from services import database
from services import ml_service

# Blueprint for API routes (prefix: /api)
alert_bp = Blueprint("alert", __name__, url_prefix="/api")


def parse_serial_line(line):
    """
    Parse a plain-text serial line from the ESP.
    Expected format: V: 2.42V | I: 510mA | L: 16% | T: 26.9C
    Returns a dict with voltage, current, load, temperature, and status.
    """
    result = {}

    # Extract voltage  (e.g. "V: 2.42V")
    v_match = re.search(r'V:\s*([\d.]+)V', line)
    if v_match:
        result["voltage"] = float(v_match.group(1))

    # Extract current in mA  (e.g. "I: 510mA")
    i_match = re.search(r'I:\s*([\d.]+)mA', line)
    if i_match:
        result["current"] = float(i_match.group(1))

    # Extract load percentage  (e.g. "L: 16%")
    l_match = re.search(r'L:\s*([\d.]+)%', line)
    if l_match:
        result["load"] = float(l_match.group(1))

    # Extract temperature  (e.g. "T: 26.9C")
    t_match = re.search(r'T:\s*([\d.]+)C', line)
    if t_match:
        result["temperature"] = float(t_match.group(1))

    # Auto-determine status based on readings
    result["status"] = determine_status(result)

    return result


def is_nighttime():
    """
    Check if it's currently nighttime (between NIGHT_START and NIGHT_END).
    Default: 6 PM (18:00) to 6 AM (06:00).
    """
    from datetime import datetime
    NIGHT_START = 18  # 6 PM
    NIGHT_END = 6     # 6 AM
    hour = datetime.now().hour
    return hour >= NIGHT_START or hour < NIGHT_END


def determine_status(data):
    """Determine panel status based on sensor readings."""
    voltage = data.get("voltage")
    current = data.get("current")
    temperature = data.get("temperature")
    load = data.get("load")

    # ESP sends null when sensor fails — treat as 0
    if voltage is None: voltage = 0
    if current is None: current = 0
    if temperature is None: temperature = 0
    if load is None: load = 0

    # ── Nighttime detection ──────────────────────────────────
    # At night, solar panels naturally produce near-zero voltage
    # and light readings. Don't flag these as faults.
    if is_nighttime() and voltage < 1.0 and load < 5:
        # Still check for genuine hardware faults at night
        night_faults = []
        if temperature > 60:
            night_faults.append("OVER_TEMP")
        elif temperature > 45:
            night_faults.append("HIGH_TEMP")
        if night_faults:
            return "NIGHTTIME | " + " | ".join(night_faults)
        return "NIGHTTIME_IDLE"

    # ── Daytime fault detection ──────────────────────────────
    faults = []

    # Voltage checks
    if voltage > 5.5:
        faults.append("OVER_VOLTAGE")
    elif voltage < 1.0:
        faults.append("LOW_VOLTAGE")

    # Temperature checks
    if temperature > 60:
        faults.append("OVER_TEMP")
    elif temperature > 45:
        faults.append("HIGH_TEMP")

    # Current checks
    if current > 1000:
        faults.append("OVER_CURRENT")

    # Load checks
    if load < 5:
        faults.append("LOW_LOAD")

    if faults:
        return " | ".join(faults)
    return "HEALTHY"


def normalize_json(raw):
    """
    Map ESP JSON keys to internal field names.
    ESP sends:  panel_voltage_v, current_ma, light_pct, temp_c, device, ip
    Internal:   voltage, current, load, temperature, device, ip
    """
    field_map = {
        "panel_voltage_v": "voltage",
        "current_ma":      "current",
        "light_pct":       "load",
        "temp_c":          "temperature",
    }
    normalized = {}
    for key, value in raw.items():
        new_key = field_map.get(key, key)  # rename or keep as-is
        normalized[new_key] = value
    return normalized


@alert_bp.route("/data", methods=["POST"])
def receive_data():
    content_type = (request.content_type or "").lower()

    # DEBUG: see what Flask actually received
    raw_body = request.get_data(as_text=True)  # don't strip yet
    print("---- INCOMING ----")
    print("Content-Type:", content_type)
    print("Raw body:", repr(raw_body))
    print("------------------")

    if "application/json" in content_type:
        # ESP sends nan for failed sensors — not valid JSON
        # Replace nan/NaN/Infinity with null before parsing
        cleaned = re.sub(r'\bnan\b|\bNaN\b|\bInfinity\b|\b-Infinity\b', 'null', raw_body)
        try:
            raw = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return jsonify({
                "error": "Invalid JSON",
                "hint": "Send valid JSON with Content-Type: application/json"
            }), 400
        data = normalize_json(raw)

    else:
        raw_text = raw_body.strip()
        if not raw_text:
            return jsonify({"error": "Empty data received"}), 400

        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        data = parse_serial_line(lines[-1])

    # Defaults
    data.setdefault("panel_id", data.get("device", "PANEL-1"))
    data.setdefault("status", determine_status(data))

    # ── ML anomaly detection ─────────────────────────────────
    ml_result = ml_service.predict(data)
    data["ml_prediction"] = ml_result

    # If ML detects anomaly and rules say HEALTHY, flag it
    if ml_result["is_anomaly"] and data["status"] == "HEALTHY":
        data["status"] = "ML_ANOMALY"

    print("📡 PARSED DATA:", data)
    print("🌲 ML PREDICTION:", ml_result)

    try:
        database.insert_alert(data)
    except Exception as e:
        print("Error inserting alert:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Data received", "received": data}), 200


@alert_bp.route("/alerts", methods=["GET"])
def get_alerts():
    rows = database.get_recent_alerts(50)
    # rows: list of tuples (panel_id, voltage, current, load, temperature, status, timestamp)
    alerts = []
    for r in rows:
        alerts.append({
            "panel_id": r[0],
            "voltage": r[1],
            "current": r[2],
            "load": r[3],
            "temperature": r[4],
            "status": r[5],
            "timestamp": r[6]
        })
    return jsonify({"alerts": alerts}), 200


# ── ML Endpoints ──────────────────────────────────────────────

@alert_bp.route("/ml/predict", methods=["POST"])
def ml_predict():
    """
    Predict anomaly for a single reading.
    Body: {"voltage": 3.2, "current": 450, "load": 50, "temperature": 28}
    """
    data = request.get_json(force=True)
    result = ml_service.predict(data)
    return jsonify(result), 200


@alert_bp.route("/ml/predict/batch", methods=["POST"])
def ml_predict_batch():
    """
    Predict anomalies for multiple readings.
    Body: {"readings": [{...}, {...}, ...]}
    """
    body = request.get_json(force=True)
    readings = body.get("readings", [])
    if not readings:
        return jsonify({"error": "No readings provided"}), 400
    results = ml_service.predict_batch(readings)
    return jsonify({"predictions": results}), 200


@alert_bp.route("/ml/status", methods=["GET"])
def ml_status():
    """Check if the Isolation Forest model is loaded and ready."""
    return jsonify({
        "model_loaded": ml_service.is_model_loaded(),
        "model_path": ml_service.MODEL_PATH,
        "features": ml_service.FEATURE_NAMES,
    }), 200


@alert_bp.route("/ml/train", methods=["POST"])
def ml_train():
    """
    Trigger model re-training from the database.
    Optional body: {"contamination": 0.1, "n_estimators": 200}
    """
    body = request.get_json(silent=True) or {}
    contamination = body.get("contamination", 0.1)
    n_estimators = body.get("n_estimators", 200)

    # Load data from DB
    import sqlite3
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT voltage, current, load_pct, temperature
        FROM alerts
        WHERE voltage IS NOT NULL
          AND current IS NOT NULL
          AND load_pct IS NOT NULL
          AND temperature IS NOT NULL
    """)
    rows = cur.fetchall()
    conn.close()

    data = [{
        "voltage": r[0], "current": r[1],
        "load": r[2], "temperature": r[3]
    } for r in rows]

    try:
        metrics = ml_service.train_model(
            data,
            contamination=contamination,
            n_estimators=n_estimators,
        )
        return jsonify({"message": "Model trained successfully", "metrics": metrics}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
