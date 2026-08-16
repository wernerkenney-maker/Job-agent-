#!/usr/bin/env python3
"""Fetch open job listings from Ashby-hosted company job boards.

Search notes: checked ~20 candidates (Iambic Therapeutics, myTomorrows,
Paradigm, Unlearn, Triomics, and more) -- real companies, but none with
Brazil/LATAM-eligible postings as of this check. One repeat hit, "The
Global Talent Co.", was deliberately excluded: it's a staffing agency
placing candidates across unrelated industries (music-industry valuation,
customer care, marketing), not a CRO/biotech/pharma employer. COMPANIES
is empty for now; add a token here as soon as a genuine match turns up.
"""

import requests

COMPANIES = {}

ASHBY_URL_TEMPLATE = "https://api.ashbyhq.com/posting-api/job-board/{token}"


def fetch_jobs(token):
    url = ASHBY_URL_TEMPLATE.format(token=token)
    response = requests.get(url, params={"includeCompensation": "true"}, timeout=30)
    response.raise_for_status()
    return response.json().get("jobs", [])


def main():
    if not COMPANIES:
        print("No Ashby companies configured yet.")
        return
    for token, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            jobs = fetch_jobs(token)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue

        print(f"{len(jobs)} open jobs\n")
        for job in jobs:
            print(job["title"])
            print(job.get("jobUrl") or job.get("applyUrl"))
            print()


if __name__ == "__main__":
    main()
