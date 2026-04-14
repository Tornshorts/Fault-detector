#!/usr/bin/env python3
"""
Test suite for BOTH ML models:
  - Isolation Forest (anomaly detection)
  - Random Forest (fault classification)
  - Combined predictions

Run:  python test_models.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ml_service import (
    # Isolation Forest
    if_predict, if_predict_batch, load_if_model, is_if_model_loaded,
    # Random Forest
    rf_predict, rf_predict_batch, load_rf_model, is_rf_model_loaded,
    # Combined
    predict, predict_batch, get_status,
    FEATURE_NAMES,
)


def header(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def test_result(name, passed, detail=""):
    icon = "✅" if passed else "❌"
    detail_str = f" — {detail}" if detail else ""
    print(f"  {icon} {name}{detail_str}")
    return passed


def run_tests():
    results = {"passed": 0, "failed": 0}

    def track(name, passed, detail=""):
        p = test_result(name, passed, detail)
        if p:
            results["passed"] += 1
        else:
            results["failed"] += 1

    # ═══════════════════════════════════════════════════════
    header("1. Model Loading")
    # ═══════════════════════════════════════════════════════
    if_loaded = load_if_model()
    track("Isolation Forest loads from disk", if_loaded)
    track("is_if_model_loaded() returns True", is_if_model_loaded())

    rf_loaded = load_rf_model()
    track("Random Forest loads from disk", rf_loaded)
    track("is_rf_model_loaded() returns True", is_rf_model_loaded())

    status = get_status()
    track("get_status() returns both models", 
          "isolation_forest" in status and "random_forest" in status,
          f"keys={list(status.keys())}")

    # ═══════════════════════════════════════════════════════
    header("2. Isolation Forest — Normal Readings")
    # ═══════════════════════════════════════════════════════
    normal_cases = [
        {"name": "Typical healthy panel",
         "reading": {"voltage": 2.5, "current": 300, "load": 40, "temperature": 25}},
        {"name": "Low but plausible voltage",
         "reading": {"voltage": 0.5, "current": 50, "load": 10, "temperature": 24}},
        {"name": "Night idle (common pattern)",
         "reading": {"voltage": 0.0, "current": 0, "load": 0, "temperature": 25}},
    ]
    for case in normal_cases:
        result = if_predict(case["reading"])
        track(
            f"IF: {case['name']}",
            result["label"] in ("NORMAL", "ANOMALY"),
            f"label={result['label']}, score={result['anomaly_score']}"
        )

    # ═══════════════════════════════════════════════════════
    header("3. Isolation Forest — Anomalous Readings")
    # ═══════════════════════════════════════════════════════
    anomaly_cases = [
        {"name": "Extreme voltage spike",
         "reading": {"voltage": 50, "current": 300, "load": 40, "temperature": 25}},
        {"name": "Massive current",
         "reading": {"voltage": 2.0, "current": 10000, "load": 50, "temperature": 25}},
        {"name": "All extreme values",
         "reading": {"voltage": 100, "current": 50000, "load": 500, "temperature": 200}},
        {"name": "Negative values everywhere",
         "reading": {"voltage": -10, "current": -500, "load": -100, "temperature": -30}},
    ]
    for case in anomaly_cases:
        result = if_predict(case["reading"])
        track(
            f"IF: {case['name']}",
            result["is_anomaly"],
            f"label={result['label']}, score={result['anomaly_score']}"
        )

    # ═══════════════════════════════════════════════════════
    header("4. Isolation Forest — Score Sanity")
    # ═══════════════════════════════════════════════════════
    normal_scores = [if_predict(c["reading"])["anomaly_score"] for c in normal_cases]
    anomaly_scores = [if_predict(c["reading"])["anomaly_score"] for c in anomaly_cases]
    avg_normal = sum(normal_scores) / len(normal_scores)
    avg_anomaly = sum(anomaly_scores) / len(anomaly_scores)
    track("IF: Normal avg score > Anomaly avg score",
          avg_normal > avg_anomaly,
          f"normal_avg={avg_normal:.4f}, anomaly_avg={avg_anomaly:.4f}")

    # ═══════════════════════════════════════════════════════
    header("5. Random Forest — Fault Classification")
    # ═══════════════════════════════════════════════════════
    rf_cases = [
        {"name": "Low voltage reading",
         "reading": {"voltage": 0.2, "current": 0, "load": 10, "temperature": 25}},
        {"name": "Healthy reading",
         "reading": {"voltage": 3.0, "current": 400, "load": 50, "temperature": 25}},
        {"name": "Over-current fault",
         "reading": {"voltage": 2.0, "current": 1500, "load": 50, "temperature": 25}},
        {"name": "High temperature",
         "reading": {"voltage": 2.0, "current": 300, "load": 50, "temperature": 55}},
    ]
    for case in rf_cases:
        result = rf_predict(case["reading"])
        has_required = all(k in result for k in ["predicted_status", "confidence", "probabilities"])
        track(
            f"RF: {case['name']}",
            has_required and result["predicted_status"] != "NO_MODEL",
            f"status={result['predicted_status']}, conf={result['confidence']}"
        )

    # ═══════════════════════════════════════════════════════
    header("6. Random Forest — Batch Predictions")
    # ═══════════════════════════════════════════════════════
    batch = [c["reading"] for c in rf_cases]
    batch_results = rf_predict_batch(batch)
    track("RF batch returns correct count",
          len(batch_results) == len(batch),
          f"expected={len(batch)}, got={len(batch_results)}")

    statuses = [r["predicted_status"] for r in batch_results]
    track("RF batch all have status",
          all(s != "NO_MODEL" for s in statuses),
          f"statuses={statuses}")

    # ═══════════════════════════════════════════════════════
    header("7. Combined Predictions (Both Models)")
    # ═══════════════════════════════════════════════════════
    combined_cases = [
        {"name": "Normal reading",
         "reading": {"voltage": 2.5, "current": 300, "load": 40, "temperature": 25}},
        {"name": "Extreme anomaly",
         "reading": {"voltage": 100, "current": 50000, "load": 500, "temperature": 200}},
    ]
    for case in combined_cases:
        result = predict(case["reading"])
        has_both = "isolation_forest" in result and "random_forest" in result and "combined_status" in result
        track(
            f"Combined: {case['name']}",
            has_both,
            f"IF={result['isolation_forest']['label']}, "
            f"RF={result['random_forest']['predicted_status']}, "
            f"combined={result['combined_status']}"
        )

    # Combined batch
    batch = [c["reading"] for c in combined_cases]
    batch_results = predict_batch(batch)
    track("Combined batch returns correct count",
          len(batch_results) == len(batch))
    track("Combined batch has all fields",
          all("isolation_forest" in r and "random_forest" in r and "combined_status" in r
              for r in batch_results))

    # ═══════════════════════════════════════════════════════
    header("8. Edge Cases")
    # ═══════════════════════════════════════════════════════
    result = predict({"voltage": 2.0})  # missing keys
    track("Missing keys handled",
          "isolation_forest" in result and "random_forest" in result)

    result = predict({"voltage": None, "current": None, "load": None, "temperature": None})
    track("None values handled",
          "isolation_forest" in result and "random_forest" in result)

    result = predict({})
    track("Empty dict handled",
          "isolation_forest" in result and "random_forest" in result)

    # ═══════════════════════════════════════════════════════
    header("9. API Integration (Flask test client)")
    # ═══════════════════════════════════════════════════════
    try:
        from run import app
        client = app.test_client()

        # ML status
        resp = client.get("/api/ml/status")
        track("GET /api/ml/status", resp.status_code == 200,
              f"status={resp.status_code}")

        # Combined predict
        resp = client.post("/api/ml/predict", json={
            "voltage": 2.5, "current": 300, "load": 40, "temperature": 25
        })
        track("POST /api/ml/predict (combined)", resp.status_code == 200,
              f"status={resp.status_code}")

        # IF predict
        resp = client.post("/api/ml/predict/if", json={
            "voltage": 2.5, "current": 300, "load": 40, "temperature": 25
        })
        track("POST /api/ml/predict/if", resp.status_code == 200,
              f"status={resp.status_code}")

        # RF predict
        resp = client.post("/api/ml/predict/rf", json={
            "voltage": 2.5, "current": 300, "load": 40, "temperature": 25
        })
        track("POST /api/ml/predict/rf", resp.status_code == 200,
              f"status={resp.status_code}")

        # Batch predict
        resp = client.post("/api/ml/predict/batch", json={
            "readings": [
                {"voltage": 2.0, "current": 200, "load": 30, "temperature": 25},
                {"voltage": 100, "current": 50000, "load": 500, "temperature": 200},
            ]
        })
        track("POST /api/ml/predict/batch", resp.status_code == 200,
              f"status={resp.status_code}")

        # ESP data ingestion (should trigger both models)
        resp = client.post("/api/data", json={
            "panel_voltage_v": 3.5, "current_ma": 400,
            "light_pct": 60, "temp_c": 26, "device": "PANEL-TEST"
        })
        track("POST /api/data (ESP ingestion with ML)", resp.status_code == 200,
              f"status={resp.status_code}")
        if resp.status_code == 200:
            body = resp.get_json()
            has_ml = "ml_prediction" in body.get("received", {})
            track("ESP response includes ml_prediction", has_ml)

    except Exception as e:
        track("API integration", False, f"error: {e}")

    # ═══════════════════════════════════════════════════════
    header("SUMMARY")
    # ═══════════════════════════════════════════════════════
    total = results["passed"] + results["failed"]
    print(f"\n  ✅ Passed: {results['passed']}/{total}")
    print(f"  ❌ Failed: {results['failed']}/{total}")
    if results["failed"] == 0:
        print("\n  🎉 All tests passed — both models running frictionlessly!")
    else:
        print(f"\n  ⚠️  {results['failed']} test(s) failed")

    return results["failed"] == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
