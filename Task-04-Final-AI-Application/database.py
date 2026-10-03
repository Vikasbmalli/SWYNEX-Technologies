"""
SQLite database layer for the Final AI Application.

Stores every analysis run (history) and, per run, each flagged anomaly,
so the app has a real persistence layer instead of an in-memory demo.
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "app_data.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    filename TEXT,
    sensitivity REAL NOT NULL,
    months_analyzed INTEGER NOT NULL,
    anomalies_found INTEGER NOT NULL,
    avg_usage REAL,
    max_bill REAL,
    warnings TEXT
);

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    month TEXT NOT NULL,
    usage_kwh REAL NOT NULL,
    bill_amount REAL NOT NULL,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def save_run(filename, sensitivity, result_df, flagged_df, warnings):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO runs (created_at, filename, sensitivity, months_analyzed,
                                 anomalies_found, avg_usage, max_bill, warnings)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), filename, sensitivity, len(result_df), len(flagged_df),
             float(result_df["usage_kwh"].mean()), float(result_df["bill_amount"].max()),
             "; ".join(warnings)),
        )
        run_id = cur.lastrowid
        for _, r in flagged_df.iterrows():
            conn.execute(
                """INSERT INTO anomalies (run_id, month, usage_kwh, bill_amount, severity, reason)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (run_id, r["month"].strftime("%Y-%m-%d"), float(r["usage_kwh"]),
                 float(r["bill_amount"]), r["severity"], r["reason"]),
            )
        return run_id


def recent_runs(limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def stats_summary():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total_runs, COALESCE(SUM(anomalies_found),0) AS total_anomalies "
            "FROM runs"
        ).fetchone()
        return dict(row)
