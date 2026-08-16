#!/usr/bin/env python3
"""Mark a tracked job's status: "applied", "interested", or "pass".

Usage:
  python3 set_status.py <posting-url> <applied|interested|pass>

The URL can be any of a job's apply links (if it was deduped across
sibling company boards, any sibling's URL works). Run this, then
re-run apply_manual_scores.py or match_jobs.py to refresh report.html
with the updated status.

Marking a job "applied" also logs it (once) to applications_log.json via
pace_tracker.py, for the weekly/all-time pace stats shown in the report.
"""

import sys

from jobs_state import VALID_STATUSES, find_key_by_url, load_state, save_state
from pace_tracker import log_application


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in VALID_STATUSES:
        print(f"Usage: python3 set_status.py <posting-url> <{'|'.join(VALID_STATUSES)}>", file=sys.stderr)
        sys.exit(1)

    url, status = sys.argv[1], sys.argv[2]
    state = load_state()
    key = find_key_by_url(state, url)
    if key is None:
        print(f"No tracked job found with URL: {url}", file=sys.stderr)
        sys.exit(1)

    state[key]["status"] = status
    save_state(state)
    print(f"Marked \"{state[key]['title']}\" ({state[key]['company']}) as {status}.")

    if status == "applied":
        job = state[key]
        logged = log_application(key, job["title"], job["company"])
        if logged:
            print("Logged to applications_log.json for pace tracking.")


if __name__ == "__main__":
    main()
