"""
Isolation Forest anomaly detection for solar panel fault detection.

The model learns the "normal" operating patterns from historical sensor data
(voltage, current, load%, temperature) and flags readings that deviate
significantly from those patterns as anomalies.
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")

# Feature order used throughout the pipeline
FEATURE_NAMES = ["voltage", "current", "load", "temperature"]

# Global model & scaler (loaded once, reused per-request)
_model = None
_scaler = None


def _ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def train_model(data, contamination=0.1, n_estimators=200, random_state=42):
    """
    Train an Isolation Forest on sensor data.

    Args:
        data: list of dicts with keys matching FEATURE_NAMES,
              OR a 2D numpy array with columns in FEATURE_NAMES order.
        contamination: expected proportion of anomalies (0.0–0.5).
        n_estimators: number of isolation trees.
        random_state: seed for reproducibility.

    Returns:
        dict with training metrics.
    """
    global _model, _scaler

    # Convert list-of-dicts to numpy array
    if isinstance(data, list):
        X = np.array([
            [d.get(f, 0) or 0 for f in FEATURE_NAMES]
            for d in data
        ], dtype=np.float64)
    else:
        X = np.asarray(data, dtype=np.float64)

    if X.shape[0] < 10:
        raise ValueError(f"Need at least 10 samples to train, got {X.shape[0]}")

    # Scale features (important — voltage is ~0-5V, current is 0-2000mA)
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    # Train Isolation Forest
    _model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,  # use all CPU cores
    )
    _model.fit(X_scaled)

    # Compute training metrics
    predictions = _model.predict(X_scaled)
    scores = _model.decision_function(X_scaled)
    n_anomalies = int(np.sum(predictions == -1))
    n_normal = int(np.sum(predictions == 1))

    # Save model + scaler to disk
    _ensure_model_dir()
    joblib.dump(_model, MODEL_PATH)
    joblib.dump(_scaler, SCALER_PATH)

    return {
        "total_samples": int(X.shape[0]),
        "normal": n_normal,
        "anomalies": n_anomalies,
        "anomaly_pct": round(n_anomalies / X.shape[0] * 100, 2),
        "score_mean": round(float(np.mean(scores)), 4),
        "score_std": round(float(np.std(scores)), 4),
        "model_path": MODEL_PATH,
    }


def load_model():
    """Load a previously trained model from disk."""
    global _model, _scaler

    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return False

    _model = joblib.load(MODEL_PATH)
    _scaler = joblib.load(SCALER_PATH)
    return True


def predict(reading):
    """
    Predict whether a single sensor reading is normal or anomalous.

    Args:
        reading: dict with keys matching FEATURE_NAMES.

    Returns:
        dict with:
          - is_anomaly: bool
          - anomaly_score: float (lower = more anomalous, negative = anomaly)
          - label: "NORMAL" or "ANOMALY"
          - confidence: float 0-1 (how confident the model is)
    """
    global _model, _scaler

    # Auto-load if not yet in memory
    if _model is None or _scaler is None:
        if not load_model():
            return {
                "is_anomaly": False,
                "anomaly_score": None,
                "label": "NO_MODEL",
                "confidence": 0.0,
            }

    # Build feature vector
    x = np.array([[
        reading.get(f, 0) or 0 for f in FEATURE_NAMES
    ]], dtype=np.float64)

    x_scaled = _scaler.transform(x)

    # predict: 1 = normal, -1 = anomaly
    pred = int(_model.predict(x_scaled)[0])
    # decision_function: negative = anomaly, positive = normal
    score = float(_model.decision_function(x_scaled)[0])

    # Convert score to a 0-1 confidence value
    # Score near 0 = borderline; large positive = clearly normal; large negative = clearly anomalous
    confidence = min(1.0, abs(score) / 0.3)  # normalize roughly

    return {
        "is_anomaly": bool(pred == -1),
        "anomaly_score": round(score, 4),
        "label": "ANOMALY" if pred == -1 else "NORMAL",
        "confidence": round(confidence, 2),
    }


def predict_batch(readings):
    """
    Predict anomalies for a batch of readings.

    Args:
        readings: list of dicts with keys matching FEATURE_NAMES.

    Returns:
        list of prediction dicts (same format as predict()).
    """
    global _model, _scaler

    if _model is None or _scaler is None:
        if not load_model():
            return [{"is_anomaly": False, "anomaly_score": None,
                      "label": "NO_MODEL", "confidence": 0.0}
                    for _ in readings]

    X = np.array([
        [r.get(f, 0) or 0 for f in FEATURE_NAMES]
        for r in readings
    ], dtype=np.float64)

    X_scaled = _scaler.transform(X)
    preds = _model.predict(X_scaled)
    scores = _model.decision_function(X_scaled)

    results = []
    for pred, score in zip(preds, scores):
        p = int(pred)
        s = float(score)
        confidence = min(1.0, abs(s) / 0.3)
        results.append({
            "is_anomaly": bool(p == -1),
            "anomaly_score": round(s, 4),
            "label": "ANOMALY" if p == -1 else "NORMAL",
            "confidence": round(confidence, 2),
        })
    return results


def is_model_loaded():
    """Check if a model is available (in memory or on disk)."""
    global _model
    if _model is not None:
        return True
    return os.path.exists(MODEL_PATH)
