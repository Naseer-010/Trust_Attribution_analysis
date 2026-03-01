"""
Experiment Event Logger
=======================
Thread-safe CSV logging for experiment events.
Appends each event as a row to data/results.csv.
"""

import csv
import os
import threading
from pathlib import Path
from typing import Dict, Any

# ─── Config ──────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "results.csv"

CSV_HEADERS = [
    "participant_id",
    "condition_id",
    "agent_name",
    "tone_style",
    "confidence_framing",
    "ai_recommendation",
    "scenario_id",
    "correct_answer",
    "confidence_score",
    "decision",
    "latency_ms",
    "timestamp",
]

_lock = threading.Lock()


# ─── Public API ──────────────────────────────────────────────────────────────

def _ensure_csv_exists() -> None:
    """Create the CSV file with headers if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def log_event(data: Dict[str, Any]) -> None:
    """
    Thread-safe append of a single event row to results.csv.

    Expected keys in `data`:
        participant_id, condition_id, cue_metadata (dict with
        agent_name, tone_style, confidence_framing),
        ai_recommendation, decision, latency_ms, timestamp
    """
    with _lock:
        _ensure_csv_exists()
        cue = data.get("cue_metadata", {})
        row = [
            data.get("participant_id", ""),
            data.get("condition_id", ""),
            cue.get("agent_name", ""),
            cue.get("tone_style", ""),
            cue.get("confidence_framing", ""),
            data.get("ai_recommendation", ""),
            data.get("scenario_id", ""),
            data.get("correct_answer", ""),
            data.get("confidence_score", ""),
            data.get("decision", ""),
            data.get("latency_ms", ""),
            data.get("timestamp", ""),
        ]
        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)


def get_csv_path() -> Path:
    """Return the absolute path to the results CSV."""
    _ensure_csv_exists()
    return CSV_PATH
