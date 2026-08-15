#!/usr/bin/env python3
"""Regenerate report.html from a manually maintained set of scored matches.

Use this after a manual (conversation-based) scoring pass, e.g. when
ANTHROPIC_API_KEY isn't available to run match_jobs.py directly. Edit
manual_matches.json with the current matches, then run this script.
"""

import json

from report import write_report

with open("manual_matches.json") as f:
    data = json.load(f)

matches = sorted(data["matches"], key=lambda job: job["score"], reverse=True)

report_path = write_report(matches, data["scored_count"], data["fetched_count"])
print(f"Report written to {report_path} ({len(matches)} matches)")
