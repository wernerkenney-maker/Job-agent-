#!/usr/bin/env python3
"""Shared post-scoring pipeline: dedupe sibling postings, update the
persistent seen/status state, and backfill cover letters, resume bullet
adjustments, and salary estimates. Used identically by match_jobs.py
(live API scoring) and apply_manual_scores.py (manual scoring), so both
paths produce the same report.html shape.
"""

from datetime import datetime, timezone

from cost_of_living import (
    col_comparison_note,
    col_comparison_note_brl,
    find_city,
    parse_brl_salary_figures,
)
from cover_letter import COVER_LETTER_SCORE_THRESHOLD as DRAFT_MATERIALS_THRESHOLD
from dedup import merge_sibling_postings
from jobs_state import APPLIED_STATUSES, EXCLUDED_STATUSES, load_state, save_state, update_state
from link_check import check_link_status


def today_str():
    return datetime.now(timezone.utc).date().isoformat()


# Score is the primary sort driver, not confidence tier. Confidence only
# nudges it: "confirmed" (real disclosed pay) gets a modest boost since
# it's real money, not a guess; "flagged" (an estimate a real
# contradicting data point calls into doubt) gets a real penalty;
# "estimated" -- the normal, unremarkable default -- gets no adjustment
# either way. This is a nudge, not a tier override: a flagged 95 can
# still outrank a confirmed 80.
SALARY_CONFIDENCE_ADJUSTMENT = {"confirmed": 4, "estimated": 0, "flagged": -12}


def sort_key(job):
    adjustment = SALARY_CONFIDENCE_ADJUSTMENT.get(job.get("salary_confidence"), 0)
    return -(job["score"] + adjustment)


def process_run(
    raw_matches,
    cover_letter_fn=None,
    salary_estimate_fn=None,
    resume_bullets_fn=None,
    today=None,
):
    """raw_matches: per-posting matches (title/company/location/url/score/
    reason/salary). cover_letter_fn(job)->rel_path or None,
    resume_bullets_fn(job)->rel_path or None, salary_estimate_fn(job)->
    label string or None; all optional. Returns (new_matches,
    interested_matches, applied_matches, state). Jobs marked "pass" or
    "declined" are excluded from every returned list and permanently
    excluded from future reports -- declined never resurfaces as new
    even if the same posting is re-fetched later, since update_state()
    only refreshes an existing key's live fields, never its status."""
    today = today or today_str()
    merged = merge_sibling_postings(raw_matches)
    state = load_state()
    new_keys = update_state(state, merged, today)

    for job in state.values():
        if job["status"] in EXCLUDED_STATUSES:
            continue
        # No point drafting materials for a posting that's already gone --
        # but still refresh its salary/col-note fields below like any
        # other tracked job.
        if job["score"] >= DRAFT_MATERIALS_THRESHOLD and job.get("link_status") != "expired":
            if cover_letter_fn and not job.get("cover_letter_path"):
                path = cover_letter_fn(job)
                if path:
                    job["cover_letter_path"] = path
            if resume_bullets_fn and not job.get("resume_bullets_path"):
                path = resume_bullets_fn(job)
                if path:
                    job["resume_bullets_path"] = path
        if salary_estimate_fn and job.get("salary") == "Not disclosed" and not job.get("salary_estimate"):
            estimate = salary_estimate_fn(job)
            if estimate:
                job["salary_estimate"] = estimate

        # Disclosed pay is authoritative -- always "confirmed" regardless
        # of whatever confidence a match supplied. Otherwise fall back to
        # whatever confidence was set (e.g. "flagged" for a shakily-
        # grounded estimate), defaulting to "estimated".
        if job.get("salary") and job["salary"] != "Not disclosed":
            job["salary_confidence"] = "confirmed"
        elif not job.get("salary_confidence"):
            job["salary_confidence"] = "estimated"

        # City + cost-of-living comparison are deterministic (no API call),
        # so recompute on every run rather than backfilling once.
        city = find_city(job.get("location", ""))
        job["city"] = city
        salary_for_comparison = job.get("salary") if job.get("salary") != "Not disclosed" else job.get("salary_estimate")
        if not city:
            job["col_note"] = None
        elif job.get("market") == "Brazilian market (local)":
            figures = parse_brl_salary_figures(salary_for_comparison)
            job["col_note"] = col_comparison_note_brl(city, *figures) if figures else None
        else:
            job["col_note"] = col_comparison_note(city, salary_for_comparison)

    save_state(state)

    new_matches = [state[k] for k in new_keys if state[k]["status"] not in EXCLUDED_STATUSES]
    new_matches.sort(key=sort_key)

    interested_matches = [v for v in state.values() if v["status"] == "interested"]
    interested_matches.sort(key=sort_key)

    applied_matches = [v for v in state.values() if v["status"] in APPLIED_STATUSES]
    applied_matches.sort(key=sort_key)

    return new_matches, interested_matches, applied_matches, state


def check_expired_links(state, checker=check_link_status, today=None):
    """Daily-scan companion to process_run(): fetch every *existing*
    tracked job's primary posting URL and flag it "expired" if it now
    404s or redirects to a job-board's own "not found" page -- catching
    postings that were filled/pulled since they were first seen, not just
    finding newly-posted ones. Skips declined/passed jobs (the user's
    already done with those). A network failure never flips a job to
    expired -- check_link_status() returns "unknown" for that, which is
    left alone here. Mutates and saves state; returns the list of keys
    newly found expired this run (already-expired keys aren't repeated)."""
    today = today or today_str()
    newly_expired = []
    for key, job in state.items():
        if job["status"] in EXCLUDED_STATUSES:
            continue
        postings = job.get("postings") or []
        if not postings:
            continue
        result = checker(postings[0]["url"])
        if result == "unknown":
            continue
        was_expired = job.get("link_status") == "expired"
        job["link_status"] = result
        job["link_checked_at"] = today
        if result == "expired" and not was_expired:
            newly_expired.append(key)
    save_state(state)
    return newly_expired
