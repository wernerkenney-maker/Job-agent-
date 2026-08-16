#!/usr/bin/env python3
"""Persistent state for tracked job matches: which ones have been seen
before (so reports only surface new ones), and the user's status on each
("new", "interested", "applied", "pass").
"""

import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "jobs_state.json")
VALID_STATUSES = ("new", "interested", "applied", "pass")
TRACKED_STATUSES = ("interested", "applied")


def load_state(path=STATE_PATH):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_state(state, path=STATE_PATH):
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def update_state(state, merged_jobs, today):
    """Insert newly-seen jobs (status "new") and refresh existing ones'
    live details (score/reason/salary/postings) without touching their
    status or first_seen. Returns the list of keys that are new today."""
    new_keys = []
    for job in merged_jobs:
        key = job["key"]
        if key not in state:
            state[key] = {
                **job,
                "status": "new",
                "first_seen": today,
                "last_seen": today,
                "salary_estimate": None,
                "cover_letter_path": None,
                "resume_bullets_path": None,
                "city": None,
                "col_note": None,
            }
            new_keys.append(key)
        else:
            existing = state[key]
            for field in (
                "title", "company", "companies", "postings", "location", "score", "reason",
                "salary", "category", "probability", "trajectory", "relocation", "market", "tier",
            ):
                existing[field] = job[field]
            existing["last_seen"] = today
    return new_keys


def find_key_by_url(state, url):
    for key, job in state.items():
        for posting in job.get("postings", []):
            if posting["url"] == url:
                return key
    return None
