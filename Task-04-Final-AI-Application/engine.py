"""
Core detection engine for the Final AI Application (Task 4).
Same validated logic as Task 2/3, reused here as the model layer.
"""

import pandas as pd
from sklearn.ensemble import IsolationForest

REQUIRED_COLUMNS = ["month", "usage_kwh", "bill_amount"]
MIN_ROWS = 8


class BillError(ValueError):
    """Raised when input data can't be processed. Message is safe to show to users."""


def validate_bills(df: pd.DataFrame):
    warnings = []
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise BillError(f"Missing required column(s): {', '.join(missing)}. "
                        f"Expected: {', '.join(REQUIRED_COLUMNS)}.")

    df = df[REQUIRED_COLUMNS]
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    for col in ("usage_kwh", "bill_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    bad = df.isna().any(axis=1)
    if bad.any():
        warnings.append(f"Dropped {int(bad.sum())} row(s) with missing or non-numeric values.")
        df = df[~bad]

    if (df[["usage_kwh", "bill_amount"]] < 0).any().any():
        raise BillError("Negative usage or bill amounts found. Please check your data.")

    zero = df["usage_kwh"] == 0
    if zero.any():
        warnings.append(f"Dropped {int(zero.sum())} row(s) with 0 kWh (cannot compute rate).")
        df = df[~zero]

    if df["month"].duplicated().any():
        warnings.append("Duplicate months found; kept the last entry for each.")
        df = df.drop_duplicates("month", keep="last")

    if len(df) < MIN_ROWS:
        raise BillError(f"Need at least {MIN_ROWS} valid monthly bills, got {len(df)}.")

    return df.sort_values("month").reset_index(drop=True), warnings


def detect_anomalies(df: pd.DataFrame, sensitivity: float = 0.1):
    if not 0.01 <= sensitivity <= 0.3:
        raise BillError("Sensitivity must be between 0.01 and 0.30.")

    df = df.copy()
    df["rate_per_kwh"] = df["bill_amount"] / df["usage_kwh"]

    features = df[["usage_kwh", "rate_per_kwh"]]
    model = IsolationForest(n_estimators=200, contamination=sensitivity, random_state=42)
    df["is_anomaly"] = model.fit_predict(features) == -1
    df["score"] = -model.score_samples(features)

    med_usage = df["usage_kwh"].median()
    med_rate = df["rate_per_kwh"].median()
    reasons, severities = [], []
    for _, r in df.iterrows():
        if not r["is_anomaly"]:
            reasons.append("")
            severities.append("")
            continue
        usage_dev = (r["usage_kwh"] - med_usage) / med_usage * 100
        rate_dev = (r["rate_per_kwh"] - med_rate) / med_rate * 100
        if abs(rate_dev) > abs(usage_dev) and abs(rate_dev) > 15:
            reasons.append(f"Rate per kWh is {rate_dev:+.0f}% vs typical — possible billing error.")
        elif usage_dev > 0:
            reasons.append(f"Usage {usage_dev:+.0f}% vs typical — check appliances, AC/heater, leaks.")
        else:
            reasons.append(f"Usage {usage_dev:+.0f}% vs typical — check meter fault or vacancy.")
        big = max(abs(usage_dev), abs(rate_dev))
        severities.append("High" if big > 40 else "Medium" if big > 20 else "Low")
    df["reason"] = reasons
    df["severity"] = severities
    return df


def analyze(df: pd.DataFrame, sensitivity: float = 0.1):
    clean, warnings = validate_bills(df)
    return detect_anomalies(clean, sensitivity), warnings
