import sqlite3
import os
from datetime import datetime

# Resolve path relative to the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "solar.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)

# Create tables
def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            panel_id TEXT,
            voltage REAL,
            current REAL,
            load_pct REAL,
            temperature REAL,
            status TEXT,
            timestamp TEXT
        )
    """)
    connection.commit()
    connection.close()

# Insert alert
def insert_alert(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO alerts (
            panel_id, voltage, current, load_pct, temperature, status, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("panel_id"),
        data.get("voltage"),
        data.get("current"),
        data.get("load"),
        data.get("temperature"),
        data.get("status"),
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()

# Fetch recent alerts
def get_recent_alerts(limit=20):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT panel_id, voltage, current, load_pct, temperature, status, timestamp
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    connection.close()
    return rows
