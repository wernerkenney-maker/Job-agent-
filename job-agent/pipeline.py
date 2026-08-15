#!/usr/bin/env python3
"""Shared post-scoring pipeline: dedupe sibling postings, update the
persistent seen/status state, and backfill cover letters + salary
estimates. Used identically by match_jobs.py (live API scoring) and
apply_manual_scores.py (manual scoring), so both paths produce the same
report.html shape.
"""

from datetime import datetime, timezone

from cover_letter import COVER_LETTER_SCORE_THRESHOLD
from dedup import merge_sibling_postings
from jobs_state import TRACKED_STATUSES, load_state, save_state, update_state


def today_str():
    return datetime.now(timezone.utc).date().isoformat()


def process_run(raw_matches, cover_letter_fn=None, salary_estimate_fn=None, today=None):
    """raw_matches: per-posting matches (title/company/location/url/score/
    reason/salary). cover_letter_fn(job)->rel_path or None,
    salary_estimate_fn(job)->label string or None; both optional.
    Returns (new_matches, tracked_matches, state)."""
    today = today or today_str()
    merged = merge_sibling_postings(raw_matches)
    state = load_state()
    new_keys = update_state(state, merged, today)

    for job in state.values():
        if job["status"] == "pass":
            continue
        if cover_letter_fn and job["score"] >= COVER_LETTER_SCORE_THRESHOLD and not job.get("cover_letter_path"):
            path = cover_letter_fn(job)
            if path:
                job["cover_letter_path"] = path
        if salary_estimate_fn and job.get("salary") == "Not disclosed" and not job.get("salary_estimate"):
            estimate = salary_estimate_fn(job)
            if estimate:
                job["salary_estimate"] = estimate

    save_state(state)

    new_matches = [state[k] for k in new_keys if state[k]["status"] != "pass"]
    new_matches.sort(key=lambda j: j["score"], reverse=True)

    tracked_matches = [v for v in state.values() if v["status"] in TRACKED_STATUSES]
    tracked_matches.sort(key=lambda j: j["score"], reverse=True)

    return new_matches, tracked_matches, state
