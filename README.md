<<<<<<< HEAD
# SWYNEX-Technologies
SWYNEX-Technologies-Internship-Tasks
=======
# AI Electricity Bill Anomaly Detector — SWYNEX Task 2

**Problem:** Households/businesses often don't notice unusual electricity usage
(a spike from a leak or faulty appliance, or a drop from a meter fault) until
the bill arrives. This prototype flags unusual monthly bills automatically.

**Model used:** scikit-learn `IsolationForest` — an unsupervised anomaly
detection model. It learns the normal seasonal usage pattern and flags
months that don't fit it. No external API key is required, so nothing
secret needs to be shared. (To use a hosted AI API instead, e.g. Azure
Anomaly Detector or a custom OpenAI-based explainer, swap the model call in
`detect_anomalies()`.)

## How it works
1. `generate_sample_bills()` creates 24 months of realistic synthetic
   electricity usage data (with 3 deliberate anomalies injected).
2. `detect_anomalies()` fits IsolationForest on usage (kWh) and bill amount,
   flagging the ~12% most unusual months.
3. `explain_anomaly()` gives a plain-language reason for each flag.
4. Results are saved to `output_with_flags.csv` and a chart to
   `anomaly_chart.png`.

## Run it
```bash
pip install -r requirements.txt
python anomaly_detector.py
```

## Example output
```
Detected 3 anomalies out of 24 months:

- 2024-08: 464.8 kWh ($74.36) -> Usage 151 kWh above average — check for
  appliance left on, AC/heater overuse, or possible leak.
- 2025-04: 182.5 kWh ($29.2) -> Usage 131 kWh below average — check for
  meter fault or vacant/unused property.
- 2025-09: 517.4 kWh ($82.79) -> Usage 204 kWh above average — check for
  appliance left on, AC/heater overuse, or possible leak.
```

## Files
- `anomaly_detector.py` — main script
- `requirements.txt` — dependencies
- `output_with_flags.csv` — generated results (example run included)
- `anomaly_chart.png` — usage chart with anomalies highlighted

## Next steps (future work)
- Replace synthetic data with real utility bill exports (CSV upload).
- Add email/SMS alerts when a new bill is flagged.
- Try a hosted anomaly-detection API for comparison.
>>>>>>> b288624 (Task 2: AI Electricity Bill Anomaly Detector)
