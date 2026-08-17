#!/usr/bin/env python3
"""Regenerate report.html from a manually maintained set of scored matches.

Use this after a manual (conversation-based) scoring pass, e.g. when
ANTHROPIC_API_KEY isn't available to run match_jobs.py directly. Edit
manual_matches.json with the current per-posting matches, and
manual_extras.json with any cover letter / resume bullets text / salary
estimate figures for this run, then run this script. It goes through the
same pipeline.process_run() as match_jobs.py, so dedup, seen-job
tracking, and report generation behave identically regardless of scoring
source.
"""

import json

from br_salary_estimate import estimate_br_salary
from cover_letter import save_cover_letter
from pipeline import MIN_SCORE, check_expired_links, process_run
from report import write_report
from resume_bullets import save_resume_bullets
from salary_estimate import format_estimate

with open("manual_matches.json") as f:
    data = json.load(f)

with open("manual_extras.json") as f:
    extras = json.load(f)

cover_letters = extras.get("cover_letters", {})
resume_bullets = extras.get("resume_bullets", {})
salary_estimates = extras.get("salary_estimates", {})


def cover_letter_fn(job):
    text = cover_letters.get(job["title"])
    if not text:
        return None
    return save_cover_letter(job, text)


def resume_bullets_fn(job):
    text = resume_bullets.get(job["title"])
    if not text:
        return None
    return save_resume_bullets(job, text)


def salary_estimate_fn(job):
    if job.get("market") == "Brazilian market (local)":
        return estimate_br_salary(job["title"])
    figures = salary_estimates.get(job["title"])
    if not figures:
        return None
    return format_estimate(figures["low"], figures["high"], figures.get("note", ""))


# The API path (match_jobs.py) drops anything under MIN_SCORE before the
# pipeline ever sees it; this path historically did not, so hand-scored
# entries below the floor silently entered the report while its header
# still claimed "filtered to score 60+". Enforce the same floor here so
# the two paths agree -- but print exactly what it holds back rather than
# discarding quietly, since an invisible drop is the failure mode this
# pipeline is explicitly built to avoid.
below_floor = [m for m in data["matches"] if m["score"] < MIN_SCORE]
scored_matches = [m for m in data["matches"] if m["score"] >= MIN_SCORE]
if below_floor:
    print(f"Held back {len(below_floor)} match(es) scoring under the {MIN_SCORE} floor:")
    for m in sorted(below_floor, key=lambda m: -m["score"]):
        print(f"  [{m['score']}] {m['title']} — {m['company']}")
    print("  (still present in manual_matches.json; raise the score or lower MIN_SCORE to surface them)")

new_matches, interested_matches, applied_matches, state = process_run(
    scored_matches, cover_letter_fn, salary_estimate_fn, resume_bullets_fn
)

newly_expired = check_expired_links(state)

report_path = write_report(
    new_matches, interested_matches, applied_matches, data["scored_count"], data["fetched_count"], state
)
print(
    f"Report written to {report_path} "
    f"({len(new_matches)} new, {len(applied_matches)} applied, {len(interested_matches)} interested, "
    f"{len(newly_expired)} newly expired)"
)
if newly_expired:
    for key in newly_expired:
        print(f"  expired: {key}")
