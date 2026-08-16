#!/usr/bin/env python3
"""Log of jobs marked "applied", for tracking application pace over the
job search. Appended to by set_status.py whenever a job's status is set
to "applied" (once per job — re-marking doesn't double-log). Read by
report.py to show a weekly/all-time count in the report header.
"""

import json
import os
from datetime import datetime, timedelta, timezone

LOG_PATH = os.path.join(os.path.dirname(__file__), "applications_log.json")


def load_log(path=LOG_PATH):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_log(log, path=LOG_PATH):
    with open(path, "w") as f:
        json.dump(log, f, indent=2)


def log_application(key, title, company, when=None, path=LOG_PATH):
    """Record an application. Returns False without writing if this job
    key was already logged (avoids double-counting re-marks)."""
    log = load_log(path)
    if any(entry["key"] == key for entry in log):
        return False
    when = when or datetime.now(timezone.utc).isoformat()
    log.append({"key": key, "title": title, "company": company, "applied_at": when})
    save_log(log, path)
    return True


def _start_of_week(reference):
    start = reference - timedelta(days=reference.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)


def weekly_count(reference=None, path=LOG_PATH):
    reference = reference or datetime.now(timezone.utc)
    start = _start_of_week(reference)
    log = load_log(path)
    return sum(1 for e in log if datetime.fromisoformat(e["applied_at"]) >= start)


def total_count(path=LOG_PATH):
    return len(load_log(path))
