# Voltguard — Electricity Bill Anomaly Detector
### SWYNEX Technologies Internship — Task 4: Final AI Application

A full-stack web application that flags unusual monthly electricity bills —
sudden spikes, sudden drops, and billing errors — using machine learning.
Built on top of Task 2 and Task 3 of this internship.

---

## 1. The problem

Households and small businesses rarely notice unusual electricity usage until
the bill arrives — a leak, a stuck appliance, a faulty meter, or a billing
mistake can go unnoticed for months. This tool automates that check: give it
a history of monthly bills, and it tells you which months don't fit the
normal pattern, and why.

## 2. Method

**Model:** scikit-learn's `IsolationForest`, an unsupervised anomaly
detection algorithm. It is trained fresh on whatever data is uploaded — no
pre-trained model or external API is used, so no data ever leaves the user's
machine and no API key is required.

**Features used per month:**
- `usage_kwh` — electricity consumed
- `rate_per_kwh` — `bill_amount / usage_kwh`, which catches billing errors
  even when usage itself looks normal

**Reasoning layer:** for every flagged month, the app compares it to the
dataset's median usage and rate to generate a plain-language reason (e.g.
"Usage +87% vs typical — check appliances, AC/heater, leaks.") and a
severity (Low / Medium / High) based on how far it deviates.

**Validation layer:** all input is checked before modeling — required
columns, numeric types, negative values, duplicate months, and a minimum of
8 months of history. Bad rows are dropped with a warning where possible;
genuinely unusable input returns a clear error instead of crashing.

## 3. Architecture

```
Browser (HTML/CSS/JS, Chart.js)
        │  fetch() → multipart form (CSV + sensitivity)
        ▼
Flask backend (app.py)
        │  engine.py → validate → IsolationForest → reasons/severity
        ▼
SQLite database (app_data.db)
        runs table       — one row per analysis (file, sensitivity, totals)
        anomalies table  — one row per flagged month, linked to its run
```

- `engine.py` — model logic (validation + detection), framework-independent
- `database.py` — SQLite persistence layer (schema, save, read)
- `app.py` — Flask routes: serves the UI and a small JSON API
- `templates/index.html`, `static/style.css`, `static/script.js` — frontend
- `sample_bills.csv` — synthetic example data so the app works out of the box

## 4. Run it

```bash
pip install -r requirements.txt
python app.py
```
Open **http://localhost:5000**. The page loads with the sample data
analyzed automatically; upload your own CSV (`month, usage_kwh,
bill_amount`) or drag the sensitivity slider to see it update live.

## 5. Demo walkthrough

1. Page loads → sample data is analyzed automatically, dial and chart animate in.
2. Move the sensitivity slider → results re-run instantly.
3. Upload a CSV missing a column, or with too few rows → a popup explains
   exactly what's wrong, instead of the page breaking.
4. Click **Run history** → see every past analysis, pulled from the SQLite
   database, proving results persist across runs.

## 6. Evaluation (from Task 3)

Tested on 20 synthetic datasets with known, labeled anomalies:

| Sensitivity | Precision | Recall | F1 |
|---|---|---|---|
| 0.05 | 1.00 | 0.50 | 0.67 |
| 0.10 | 0.99 | 0.99 | 0.99 |
| 0.15 | 0.67 | 1.00 | 0.80 |
| 0.20 | 0.57 | 1.00 | 0.73 |

Sensitivity 0.10 performed best, matching the true anomaly rate in the test
data. Spikes and billing-rate errors were caught 20/20 times; sudden drops
19/20.

## 7. Limitations

- **Needs history:** at least 8 valid monthly bills are required to
  establish a baseline; fewer than that, the app refuses rather than
  guessing.
- **No trend detection:** a slow, steady rise in usage (e.g. +2%/month) is
  not flagged, because no single month looks unusual against the others —
  only sudden changes are caught.
- **No cross-household comparison:** the model is trained fresh on each
  upload; it has no sense of what's "normal" for a similar home elsewhere.
- **Sensitivity is a judgment call:** too low misses real anomalies, too
  high raises false alarms. 0.10 is a reasonable default, not a universal
  answer.
- **Synthetic evaluation only:** metrics above are from generated data with
  known answers; real-world bills may behave differently.
- **Development server:** `app.py` runs Flask's built-in server, which is
  fine for this demo but not meant for production deployment as-is.

## 8. Ethics notes

- **Not a substitute for your utility provider.** This tool flags patterns
  worth checking, not confirmed faults or billing errors. Anyone acting on
  a flagged month — disputing a bill, calling an electrician — should
  verify independently before doing so.
- **No personal or identifying data is collected.** The app only ever sees
  month, usage, and bill amount; it doesn't ask for names, addresses, or
  account numbers, and nothing is sent to any third party or external API.
- **Local-only storage.** All uploaded data and results are stored in a
  local SQLite file on the machine running the app. Nothing is transmitted
  elsewhere.
- **False positives and negatives are both possible.** The evaluation
  table above is shown deliberately so users understand the model's real
  accuracy, rather than trusting it blindly. A "High" severity flag is a
  suggestion to look closer, not a verdict.
- **Bias awareness:** the model is trained only on the data it's given. If
  a household's usage pattern is unusual for reasons unrelated to faults
  (e.g. a new appliance, working from home), it may be flagged even though
  nothing is wrong — human judgment should always be the final check.

## 9. Files

```
app.py              Flask backend & API routes
engine.py           Detection logic (validation, IsolationForest, reasons)
database.py         SQLite schema and persistence
sample_bills.csv    Example dataset
requirements.txt    Python dependencies
templates/index.html
static/style.css
static/script.js
```
