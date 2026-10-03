"""
Flask backend for the Final AI Application — Electricity Bill Anomaly Detector.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import io

import pandas as pd
from flask import Flask, jsonify, render_template, request

import database
from engine import BillError, analyze

app = Flask(__name__)
database.init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/sample")
def api_sample():
    """Serve the bundled sample dataset as JSON (used by the 'Try sample data' button)."""
    df = pd.read_csv("sample_bills.csv")
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    sensitivity = float(request.form.get("sensitivity", 0.10))
    filename = "sample_bills.csv"

    try:
        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            filename = f.filename
            raw = f.read()
            if not raw.strip():
                raise BillError("The uploaded file is empty.")
            try:
                df = pd.read_csv(io.BytesIO(raw))
            except Exception:
                raise BillError("Could not read the file as a CSV. Check the format.")
        else:
            df = pd.read_csv("sample_bills.csv")

        result, warnings = analyze(df, sensitivity)
    except BillError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:  # last-resort guard so the UI never sees a raw 500 crash
        return jsonify({"ok": False, "error": f"Unexpected error: {e}"}), 500

    flagged = result[result["is_anomaly"]].copy()
    run_id = database.save_run(filename, sensitivity, result, flagged, warnings)

    payload = {
        "ok": True,
        "run_id": run_id,
        "warnings": warnings,
        "months_analyzed": len(result),
        "anomalies_found": len(flagged),
        "avg_usage": round(float(result["usage_kwh"].mean()), 1),
        "max_bill": round(float(result["bill_amount"].max()), 2),
        "series": {
            "months": result["month"].dt.strftime("%Y-%m").tolist(),
            "usage": result["usage_kwh"].round(1).tolist(),
            "is_anomaly": result["is_anomaly"].tolist(),
        },
        "flagged": [
            {
                "month": r["month"].strftime("%Y-%m"),
                "usage_kwh": round(float(r["usage_kwh"]), 1),
                "bill_amount": round(float(r["bill_amount"]), 2),
                "severity": r["severity"],
                "reason": r["reason"],
            }
            for _, r in flagged.iterrows()
        ],
    }
    return jsonify(payload)


@app.route("/api/history")
def api_history():
    return jsonify({
        "summary": database.stats_summary(),
        "runs": database.recent_runs(10),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
