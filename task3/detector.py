"""
Core logic for the AI Electricity Bill Anomaly Detector (Task 3).

Improvements over Task 2:
  * Input validation + clear, friendly error messages (BillError)
  * New feature: cost-per-kWh rate, so billing errors are caught even when
    usage looks normal
  * Reason codes + severity for every flagged month
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

REQUIRED_COLUMNS = ["month", "usage_kwh", "bill_amount"]
MIN_ROWS = 8


class BillError(ValueError):
    """Raised when the input data cannot be processed. Message is user-friendly."""


def load_bills(source):
    """Load bills from a CSV path or an existing DataFrame, then validate."""
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        try:
            df = pd.read_csv(source)
        except FileNotFoundError:
            raise BillError(f"File not found: {source}")
        except pd.errors.EmptyDataError:
            raise BillError("The CSV file is empty.")
        except pd.errors.ParserError:
            raise BillError("The file could not be read as a CSV. Check the format.")
        except UnicodeDecodeError:
            raise BillError("The file is not a text CSV (encoding error).")
    return validate_bills(df)


def validate_bills(df: pd.DataFrame):
    """Return (clean_df, warnings). Raises BillError for unusable input."""
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
    """Flag unusual months. sensitivity = expected share of anomalies (0.01-0.3)."""
    if not 0.01 <= sensitivity <= 0.3:
        raise BillError("Sensitivity must be between 0.01 and 0.30.")

    df = df.copy()
    df["rate_per_kwh"] = df["bill_amount"] / df["usage_kwh"]

    features = df[["usage_kwh", "rate_per_kwh"]]
    model = IsolationForest(n_estimators=200, contamination=sensitivity, random_state=42)
    df["is_anomaly"] = model.fit_predict(features) == -1
    df["score"] = -model.score_samples(features)  # higher = more unusual

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
            reasons.append(f"Rate per kWh is {rate_dev:+.0f}% vs typical - possible billing error.")
        elif usage_dev > 0:
            reasons.append(f"Usage {usage_dev:+.0f}% vs typical - check appliances, AC/heater, leaks.")
        else:
            reasons.append(f"Usage {usage_dev:+.0f}% vs typical - check meter fault or vacancy.")
        big = max(abs(usage_dev), abs(rate_dev))
        severities.append("High" if big > 40 else "Medium" if big > 20 else "Low")
    df["reason"] = reasons
    df["severity"] = severities
    return df


def analyze(source, sensitivity: float = 0.1):
    """Full pipeline: load -> validate -> detect. Returns (result_df, warnings)."""
    df, warnings = load_bills(source)
    return detect_anomalies(df, sensitivity), warnings


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python detector.py <bills.csv> [sensitivity]")
        sys.exit(1)
    try:
        sens = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
        result, warns = analyze(sys.argv[1], sens)
    except (BillError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    for w in warns:
        print(f"Warning: {w}")
    flagged = result[result["is_anomaly"]]
    print(f"{len(flagged)} anomalies in {len(result)} months\n")
    for _, r in flagged.iterrows():
        print(f"{r['month']:%Y-%m}  {r['usage_kwh']:.0f} kWh  ${r['bill_amount']:.2f}  "
              f"[{r['severity']}] {r['reason']}")
