"""
AI Electricity Bill Anomaly Detector
--------------------------------------
Task 2 (Model/API Integration) prototype for SWYNEX Technologies internship.

Approach:
  - Uses scikit-learn's IsolationForest, an unsupervised ML model, to flag
    unusual electricity bill / usage readings (spikes, drops, meter errors,
    possible leaks or billing mistakes) without needing labeled fraud data.
  - No external API key required (works fully offline), but the same
    pipeline could be swapped for a hosted API (e.g. Azure Anomaly Detector)
    by replacing detect_anomalies() with an API call.

Run:
    python anomaly_detector.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_sample_bills(n_months=24, seed=42):
    """Simulate 2 years of monthly electricity bills (kWh usage + cost)."""
    rng = np.random.default_rng(seed)
    months = pd.date_range("2024-01-01", periods=n_months, freq="MS")

    # Normal seasonal usage pattern (higher in summer/winter for AC/heating)
    base = 300 + 80 * np.sin(np.linspace(0, 4 * np.pi, n_months))
    noise = rng.normal(0, 15, n_months)
    usage_kwh = base + noise

    # Inject a few realistic anomalies
    usage_kwh[7] += 220   # sudden spike (e.g. AC left running / leak)
    usage_kwh[15] -= 180  # sudden drop (e.g. vacant house / meter fault)
    usage_kwh[20] += 300  # billing error / appliance fault

    rate_per_kwh = 0.16
    cost = usage_kwh * rate_per_kwh

    df = pd.DataFrame({
        "month": months,
        "usage_kwh": usage_kwh.round(1),
        "bill_amount": cost.round(2),
    })
    return df


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Fit IsolationForest on usage + bill amount and flag anomalies."""
    model = IsolationForest(
        n_estimators=200,
        contamination=0.12,   # expect ~12% of months to be unusual
        random_state=42,
    )
    features = df[["usage_kwh", "bill_amount"]]
    df = df.copy()
    df["anomaly_score"] = model.fit_predict(features)  # -1 = anomaly, 1 = normal
    df["is_anomaly"] = df["anomaly_score"] == -1
    return df


def explain_anomaly(row, avg_usage):
    diff = row["usage_kwh"] - avg_usage
    if diff > 0:
        return f"Usage {diff:.0f} kWh above average — check for appliance left on, AC/heater overuse, or possible leak."
    else:
        return f"Usage {abs(diff):.0f} kWh below average — check for meter fault or vacant/unused property."


def main():
    df = generate_sample_bills()
    result = detect_anomalies(df)
    avg_usage = df["usage_kwh"].mean()

    print("=== AI Electricity Bill Anomaly Detector ===\n")
    print("Sample input (first 5 months):")
    print(df.head().to_string(index=False))

    anomalies = result[result["is_anomaly"]]
    print(f"\nDetected {len(anomalies)} anomalies out of {len(df)} months:\n")

    for _, row in anomalies.iterrows():
        print(f"- {row['month'].strftime('%Y-%m')}: "
              f"{row['usage_kwh']} kWh (${row['bill_amount']}) "
              f"-> {explain_anomaly(row, avg_usage)}")

    result.to_csv("output_with_flags.csv", index=False)
    print("\nFull results saved to output_with_flags.csv")

    # Simple visualization
    plt.figure(figsize=(9, 4.5))
    plt.plot(result["month"], result["usage_kwh"], label="Usage (kWh)", color="#2563eb")
    plt.scatter(anomalies["month"], anomalies["usage_kwh"], color="red", zorder=5, label="Anomaly")
    plt.title("Electricity Usage with Detected Anomalies")
    plt.xlabel("Month")
    plt.ylabel("kWh")
    plt.legend()
    plt.tight_layout()
    plt.savefig("anomaly_chart.png", dpi=150)
    print("Chart saved to anomaly_chart.png")


if __name__ == "__main__":
    main()
