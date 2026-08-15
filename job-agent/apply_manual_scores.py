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

from cover_letter import save_cover_letter
from pipeline import process_run
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
    figures = salary_estimates.get(job["title"])
    if not figures:
        return None
    return format_estimate(figures["low"], figures["high"], figures.get("note", ""))


new_matches, tracked_matches, state = process_run(
    data["matches"], cover_letter_fn, salary_estimate_fn, resume_bullets_fn
)

report_path = write_report(new_matches, tracked_matches, data["scored_count"], data["fetched_count"])
print(f"Report written to {report_path} ({len(new_matches)} new, {len(tracked_matches)} tracked)")
