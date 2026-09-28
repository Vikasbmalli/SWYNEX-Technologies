# Task 3: Intelligent Feature - Electricity Bill Anomaly Detector

Builds on Task 2 by making the detector more intelligent and robust.

## What's new
- **Rate-per-kWh feature:** catches billing errors even when usage looks normal.
- **Reason + severity** for each flagged month (High / Medium / Low).
- **Error handling:** clear messages for missing files, empty files, missing columns, too few rows, negative values, bad settings. Messy rows are dropped with a warning instead of crashing.
- **Evaluation:** precision / recall / F1 on labeled synthetic data (see `evaluation_results.txt`).
- **Failure cases:** documented, including a known limitation (slow drift).
- **Simple interface:** Streamlit web app + command-line mode.

## Run
```bash
pip install -r requirements.txt
python evaluate.py                       # evaluation + failure cases
python detector.py sample_bills.csv 0.1  # command-line demo
streamlit run app.py                     # web interface
```

## Input format
CSV with columns `month`, `usage_kwh`, `bill_amount`.

## Results (20 synthetic datasets, 4 true anomalies each)
| Sensitivity | Precision | Recall | F1 |
|---|---|---|---|
| 0.05 | 1.00 | 0.50 | 0.67 |
| 0.10 | 0.99 | 0.99 | 0.99 |
| 0.15 | 0.67 | 1.00 | 0.80 |
| 0.20 | 0.57 | 1.00 | 0.73 |

Best at sensitivity 0.10, which matches the true anomaly rate. Too low misses
anomalies; too high raises false alarms. Spikes and rate errors were caught
20/20 times, drops 19/20.

## Example output
```
4 anomalies in 36 months

2023-06  568 kWh  $91.06  [High] Usage +87% vs typical - check appliances, AC/heater, leaks.
2023-08  275 kWh  $83.70  [High] Rate per kWh is +90% vs typical - possible billing error.
2024-09  20 kWh   $3.14   [High] Usage -94% vs typical - check meter fault or vacancy.
2024-12  541 kWh  $85.42  [High] Usage +78% vs typical - check appliances, AC/heater, leaks.
```

## Failure cases and limitations
- Bad input gives a friendly `BillError` message (see `evaluate.py`, Part 2).
- **Slow drift** (usage creeping up a little each month) is not reported as a trend, since no single month looks unusual.
- Results depend on the sensitivity setting; it should match how often anomalies really occur.
- Evaluated on synthetic data only; real bills may behave differently.

## Files
`detector.py` core logic | `app.py` web UI | `evaluate.py` metrics + failure cases | `data_gen.py` synthetic data | `sample_bills.csv` example input
