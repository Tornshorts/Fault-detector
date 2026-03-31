import re
import json
from datetime import datetime
from flask import request, jsonify, Blueprint
from services import database
from services.ml_model import predict_fault  # Make sure this exists and works

# Blueprint for API routes (prefix: /api)
alert_bp = Blueprint("alert", __name__, url_prefix="/api")


def parse_serial_line(line: str) -> dict:
    """
    Parse a plain-text serial line from the ESP.
    Expected format: V: 2.42V | I: 510mA | L: 16% | T: 26.9C
    Returns a dict with voltage, current, load, temperature, and status.
    """
    result = {}

    # Extract voltage (e.g., "V: 2.42V")
    v_match = re.search(r'V:\s*([\d.]+)V', line)
    if v_match:
        result["voltage"] = float(v_match.group(1))

    # Extract current in mA (e.g., "I: 510mA")
    i_match = re.search(r'I:\s*([\d.]+)mA', line)
    if i_match:
        result["current"] = float(i_match.group(1))

    # Extract load percentage (e.g., "L: 16%")
    l_match = re.search(r'L:\s*([\d.]+)%', line)
    if l_match:
        result["load"] = float(l_match.group(1))

    # Extract temperature (e.g., "T: 26.9C")
    t_match = re.search(r'T:\s*([\d.]+)C', line)
    if t_match:
        result["temperature"] = float(t_match.group(1))

    # Auto-determine status based on readings (rule-based)
    result["status"] = determine_status(result)

    return result


def is_nighttime() -> bool:
    """
    Check if it's currently nighttime (between NIGHT_START and NIGHT_END).
    Default: 6 PM (18:00) to 6 AM (06:00).
    """
    NIGHT_START = 18  # 6 PM
    NIGHT_END = 6     # 6 AM
    hour = datetime.now().hour
    return hour >= NIGHT_START or hour < NIGHT_END


def determine_status(data: dict) -> str:
    """Determine panel status based on sensor readings (rule-based)."""
    voltage = data.get("voltage") or 0
    current = data.get("current") or 0
    temperature = data.get("temperature") or 0
    load = data.get("load") or 0

    # ── Nighttime detection ──
    if is_nighttime() and voltage < 1.0 and load < 5:
        night_faults = []
        if temperature > 60:
            night_faults.append("OVER_TEMP")
        elif temperature > 45:
            night_faults.append("HIGH_TEMP")
        if night_faults:
            return "NIGHTTIME | " + " | ".join(night_faults)
        return "NIGHTTIME_IDLE"

    # ── Daytime fault detection ──
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


def normalize_json(raw: dict) -> dict:
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
        new_key = field_map.get(key, key)
        normalized[new_key] = value
    return normalized


@alert_bp.route("/data", methods=["POST"])
def receive_data():
    content_type = (request.content_type or "").lower()

    # DEBUG: see what Flask actually received
    raw_body = request.get_data(as_text=True)
    print("---- INCOMING ----")
    print("Content-Type:", content_type)
    print("Raw body:", repr(raw_body))
    print("------------------")

    if "application/json" in content_type:
        # ESP sends nan/Infinity — replace with null before parsing
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

    # ── Combine rule-based and ML status ──
    rule_status = determine_status(data)
    ml_status = predict_fault(data)  # Must accept the `data` dict
    data["status"] = f"RULE: {rule_status} | ML: {ml_status}"

    print("📡 PARSED DATA:", data)

    try:
        database.insert_alert(data)
    except Exception as e:
        print("Error inserting alert:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Data received", "received": data}), 200


@alert_bp.route("/alerts", methods=["GET"])
def get_alerts():
    rows = database.get_recent_alerts(50)
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