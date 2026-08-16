#!/usr/bin/env python3
"""Mark a tracked job's status: "new", "interested", "applied",
"interviewing", "declined", or "pass".

Usage:
  python3 set_status.py <posting-url> <applied|interested|interviewing|declined|pass>

The URL can be any of a job's apply links (if it was deduped across
sibling company boards, any sibling's URL works). Run this, then
re-run apply_manual_scores.py or match_jobs.py to refresh report.html
with the updated status.

Report placement: "new" stays in New matches; "interested" moves to the
Interested section; "applied" and "interviewing" both move to the
Applied section (interviewing flagged distinctly there -- it's a later
stage of the same application, not a separate track); "declined" and
"pass" are permanently excluded from every report section going
forward, including if the same posting is re-fetched on a later run.

Marking a job "applied" or "interviewing" also logs it (once per job)
to applications_log.json via pace_tracker.py, for the weekly/all-time
pace stats shown in the report -- so jumping straight to "interviewing"
without ever setting "applied" still counts correctly.
"""

import sys

from jobs_state import APPLIED_STATUSES, VALID_STATUSES, find_key_by_url, load_state, save_state
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

    if status in APPLIED_STATUSES:
        job = state[key]
        logged = log_application(key, job["title"], job["company"])
        if logged:
            print("Logged to applications_log.json for pace tracking.")


if __name__ == "__main__":
    main()
