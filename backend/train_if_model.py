#!/usr/bin/env python3
"""
Train the Isolation Forest model on historical sensor data from the SQLite DB.

Usage:
    python train_model.py                     # default: 10% contamination
    python train_model.py --contamination 0.15 # custom contamination rate
"""

import argparse
import sqlite3
import os
import sys

# Add backend dir to path so imports work when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ml_service import train_if_model, FEATURE_NAMES

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "solar.db"
)


def load_training_data():
    """Load all sensor readings from the database."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
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

    # Convert to list of dicts
    data = []
    for row in rows:
        data.append({
            "voltage": row[0],
            "current": row[1],
            "load": row[2],
            "temperature": row[3],
        })

    return data


def main():
    parser = argparse.ArgumentParser(description="Train Isolation Forest model")
    parser.add_argument(
        "--contamination", type=float, default=0.1,
        help="Expected proportion of anomalies (0.01 to 0.5, default: 0.1)"
    )
    parser.add_argument(
        "--n-estimators", type=int, default=200,
        help="Number of isolation trees (default: 200)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🌲 Isolation Forest — Training Pipeline")
    print("=" * 60)

    # 1. Load data
    print("\n📂 Loading sensor data from database...")
    data = load_training_data()
    print(f"   Loaded {len(data)} readings")

    if len(data) < 10:
        print("❌ Not enough data to train (need at least 10 readings)")
        sys.exit(1)

    # 2. Show data summary
    import numpy as np
    X = [[d[f] for f in FEATURE_NAMES] for d in data]
    X = np.array(X)
    print("\n📊 Data Summary:")
    for i, name in enumerate(FEATURE_NAMES):
        col = X[:, i]
        print(f"   {name:>12s}: min={col.min():8.2f}  max={col.max():8.2f}  "
              f"mean={col.mean():8.2f}  std={col.std():8.2f}")

    # 3. Train
    print(f"\n🏋️ Training Isolation Forest...")
    print(f"   contamination = {args.contamination}")
    print(f"   n_estimators  = {args.n_estimators}")

    metrics = train_if_model(
        data,
        contamination=args.contamination,
        n_estimators=args.n_estimators,
    )

    # 4. Results
    print("\n✅ Training Complete!")
    print(f"   Total samples:  {metrics['total_samples']}")
    print(f"   Normal:         {metrics['normal']}")
    print(f"   Anomalies:      {metrics['anomalies']} ({metrics['anomaly_pct']}%)")
    print(f"   Score mean:     {metrics['score_mean']}")
    print(f"   Score std:      {metrics['score_std']}")
    print(f"   Model saved to: {metrics['model_path']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
