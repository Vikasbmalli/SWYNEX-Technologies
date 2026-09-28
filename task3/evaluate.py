"""
Evaluation examples + failure cases for the anomaly detector.

Part 1: precision / recall / F1 across 20 random datasets at several sensitivities.
Part 2: failure cases - bad inputs that must produce a clear error, not a crash.

Run:  python evaluate.py
"""

import io
import numpy as np
import pandas as pd

from data_gen import make_bills
from detector import BillError, analyze, detect_anomalies, validate_bills


def prf(true, pred):
    tp = int((true & pred).sum())
    fp = int((~true & pred).sum())
    fn = int((true & ~pred).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def part1_metrics():
    print("=" * 60)
    print("PART 1: Detection quality (20 synthetic datasets, 36 months, 4 true anomalies)")
    print("=" * 60)
    print(f"{'sensitivity':<13}{'precision':>10}{'recall':>10}{'F1':>10}")
    for sens in (0.05, 0.10, 0.15, 0.20):
        ps, rs, fs = [], [], []
        for seed in range(20):
            data = make_bills(seed=seed)
            truth = data["true_anomaly"].to_numpy()
            res = detect_anomalies(data.drop(columns="true_anomaly"), sens)
            p, r, f = prf(truth, res["is_anomaly"].to_numpy())
            ps.append(p); rs.append(r); fs.append(f)
        print(f"{sens:<13}{np.mean(ps):>10.2f}{np.mean(rs):>10.2f}{np.mean(fs):>10.2f}")

    print("\nBy anomaly type (sensitivity 0.10, 20 datasets):")
    found = {"spike": [0, 0], "drop": [0, 0], "rate error": [0, 0]}
    for seed in range(20):
        for name, kw in (("spike", dict(n_spikes=1, n_drops=0, n_rate_errors=0)),
                         ("drop", dict(n_spikes=0, n_drops=1, n_rate_errors=0)),
                         ("rate error", dict(n_spikes=0, n_drops=0, n_rate_errors=1))):
            data = make_bills(seed=seed, **kw)
            res = detect_anomalies(data.drop(columns="true_anomaly"), 0.10)
            hit = (data["true_anomaly"] & res["is_anomaly"]).sum()
            found[name][0] += int(hit)
            found[name][1] += 1
    for name, (hit, total) in found.items():
        print(f"  {name:<11} caught {hit}/{total}")


def part2_failures():
    print("\n" + "=" * 60)
    print("PART 2: Failure cases (each should give a clear message, not a crash)")
    print("=" * 60)
    good = make_bills(seed=1).drop(columns="true_anomaly")

    cases = {
        "Missing file": lambda: analyze("does_not_exist.csv"),
        "Empty file": lambda: analyze(io.StringIO("")),
        "Missing column": lambda: analyze(good.drop(columns="bill_amount")),
        "Too few rows": lambda: analyze(good.head(4)),
        "Negative usage": lambda: analyze(good.assign(usage_kwh=-good["usage_kwh"])),
        "Bad sensitivity": lambda: analyze(good, sensitivity=0.9),
        "Text in numbers": lambda: analyze(good.assign(usage_kwh=["abc"] * len(good))),
    }
    for name, fn in cases.items():
        try:
            fn()
            print(f"[??] {name}: no error raised (unexpected)")
        except BillError as e:
            print(f"[OK] {name}: {e}")
        except Exception as e:  # anything else is a real bug
            print(f"[BUG] {name}: {type(e).__name__}: {e}")

    # Recoverable case: bad rows are dropped with a warning instead of failing
    messy = good.copy()
    messy["usage_kwh"] = messy["usage_kwh"].astype(object)
    messy.loc[2, "usage_kwh"] = "n/a"
    messy.loc[5, "bill_amount"] = np.nan
    _, warns = validate_bills(messy)
    print(f"[OK] Messy rows (recoverable): {warns[0]}")

    print("\nKnown limitation: a slow drift (usage rising 2% every month) is not detected as a")
    print("trend, because no single month looks unusual to IsolationForest.")
    drift = good.copy()
    drift["usage_kwh"] = 300 * (1.02 ** np.arange(len(drift)))
    drift["bill_amount"] = drift["usage_kwh"] * 0.16
    n = int(detect_anomalies(drift, 0.05)["is_anomaly"].sum())
    print(f"  It only flagged {n} extreme end-of-range months, and never reports the upward trend.")


if __name__ == "__main__":
    part1_metrics()
    part2_failures()
