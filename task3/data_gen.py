"""Generate synthetic monthly bills with known (labeled) anomalies."""

import numpy as np
import pandas as pd


def make_bills(n_months=36, seed=0, n_spikes=2, n_drops=1, n_rate_errors=1):
    rng = np.random.default_rng(seed)
    months = pd.date_range("2023-01-01", periods=n_months, freq="MS")
    usage = 300 + 70 * np.sin(np.linspace(0, 2 * np.pi * n_months / 12, n_months))
    usage = usage + rng.normal(0, 12, n_months)
    rate = 0.16 + rng.normal(0, 0.003, n_months)
    label = np.zeros(n_months, dtype=bool)

    idx = rng.choice(np.arange(3, n_months), n_spikes + n_drops + n_rate_errors, replace=False)
    spikes, drops, rates = (idx[:n_spikes], idx[n_spikes:n_spikes + n_drops],
                            idx[n_spikes + n_drops:])
    usage[spikes] += 250
    usage[drops] -= 190
    rate[rates] *= 1.9          # billing error: usage normal, rate way off
    label[idx] = True

    return pd.DataFrame({
        "month": months,
        "usage_kwh": usage.round(1),
        "bill_amount": (usage * rate).round(2),
        "true_anomaly": label,
    })


if __name__ == "__main__":
    df = make_bills(seed=7)
    df.drop(columns="true_anomaly").to_csv("sample_bills.csv", index=False)
    print("Wrote sample_bills.csv")
