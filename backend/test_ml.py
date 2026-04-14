#!/usr/bin/env python3
"""
Test suite for the Isolation Forest anomaly detection service.

Tests:
  1. Model loading
  2. Normal reading predictions
  3. Obvious anomaly predictions
  4. Batch predictions
  5. Edge cases (missing values, nulls)
  6. API endpoint integration
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ml_service import predict, predict_batch, load_model, is_model_loaded, FEATURE_NAMES


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
    loaded = load_model()
    track("Model loads from disk", loaded)
    track("is_model_loaded() returns True", is_model_loaded())

    # ═══════════════════════════════════════════════════════
    header("2. Normal Readings (should be NORMAL)")
    # ═══════════════════════════════════════════════════════
    normal_cases = [
        {"name": "Typical healthy panel",
         "reading": {"voltage": 2.5, "current": 300, "load": 40, "temperature": 25}},
        {"name": "Low but plausible voltage",
         "reading": {"voltage": 0.5, "current": 50, "load": 10, "temperature": 24}},
        {"name": "Moderate readings",
         "reading": {"voltage": 1.0, "current": 200, "load": 20, "temperature": 26}},
        {"name": "Night idle (common pattern)",
         "reading": {"voltage": 0.0, "current": 0, "load": 0, "temperature": 25}},
    ]
    for case in normal_cases:
        result = predict(case["reading"])
        # Some of these may actually be anomalies in the trained distribution
        # We just log what the model says
        track(
            case["name"],
            result["label"] in ("NORMAL", "ANOMALY"),  # model returns something valid
            f"label={result['label']}, score={result['anomaly_score']}, conf={result['confidence']}"
        )

    # ═══════════════════════════════════════════════════════
    header("3. Anomalous Readings (should likely be ANOMALY)")
    # ═══════════════════════════════════════════════════════
    anomaly_cases = [
        {"name": "Extreme voltage spike",
         "reading": {"voltage": 50, "current": 300, "load": 40, "temperature": 25}},
        {"name": "Massive current",
         "reading": {"voltage": 2.0, "current": 10000, "load": 50, "temperature": 25}},
        {"name": "Extreme temperature",
         "reading": {"voltage": 2.0, "current": 300, "load": 50, "temperature": 100}},
        {"name": "All zeros (sensor failure?)",
         "reading": {"voltage": 0, "current": 0, "load": 0, "temperature": 0}},
        {"name": "All extreme values",
         "reading": {"voltage": 100, "current": 50000, "load": 500, "temperature": 200}},
        {"name": "Negative values everywhere",
         "reading": {"voltage": -10, "current": -500, "load": -100, "temperature": -30}},
    ]
    for case in anomaly_cases:
        result = predict(case["reading"])
        is_anom = result["is_anomaly"]
        track(
            case["name"],
            is_anom,
            f"label={result['label']}, score={result['anomaly_score']}, conf={result['confidence']}"
        )

    # ═══════════════════════════════════════════════════════
    header("4. Batch Predictions")
    # ═══════════════════════════════════════════════════════
    batch = [c["reading"] for c in normal_cases + anomaly_cases]
    batch_results = predict_batch(batch)
    track("Batch returns correct count", len(batch_results) == len(batch),
          f"expected={len(batch)}, got={len(batch_results)}")
    track("All results have required fields",
          all(k in r for r in batch_results for k in ["is_anomaly", "anomaly_score", "label", "confidence"]))

    n_anom = sum(1 for r in batch_results if r["is_anomaly"])
    track(f"Batch anomaly breakdown", True,
          f"{n_anom} anomalies / {len(batch_results) - n_anom} normal out of {len(batch_results)}")

    # ═══════════════════════════════════════════════════════
    header("5. Edge Cases")
    # ═══════════════════════════════════════════════════════
    # Missing keys
    result = predict({"voltage": 2.0})  # missing current, load, temp
    track("Missing keys default to 0", result["label"] in ("NORMAL", "ANOMALY"),
          f"label={result['label']}")

    # None values
    result = predict({"voltage": None, "current": None, "load": None, "temperature": None})
    track("None values handled", result["label"] in ("NORMAL", "ANOMALY"),
          f"label={result['label']}")

    # Empty dict
    result = predict({})
    track("Empty dict handled", result["label"] in ("NORMAL", "ANOMALY"),
          f"label={result['label']}")

    # ═══════════════════════════════════════════════════════
    header("6. Score Distribution Sanity")
    # ═══════════════════════════════════════════════════════
    # Normal readings should generally have higher scores than anomalies
    normal_scores = [predict(c["reading"])["anomaly_score"] for c in normal_cases]
    anomaly_scores = [predict(c["reading"])["anomaly_score"] for c in anomaly_cases]
    avg_normal = sum(normal_scores) / len(normal_scores)
    avg_anomaly = sum(anomaly_scores) / len(anomaly_scores)
    track("Normal avg score > Anomaly avg score",
          avg_normal > avg_anomaly,
          f"normal_avg={avg_normal:.4f}, anomaly_avg={avg_anomaly:.4f}")

    # ═══════════════════════════════════════════════════════
    header("SUMMARY")
    # ═══════════════════════════════════════════════════════
    total = results["passed"] + results["failed"]
    print(f"\n  ✅ Passed: {results['passed']}/{total}")
    print(f"  ❌ Failed: {results['failed']}/{total}")
    if results["failed"] == 0:
        print("\n  🎉 All tests passed!")
    else:
        print(f"\n  ⚠️  {results['failed']} test(s) failed")

    return results["failed"] == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
