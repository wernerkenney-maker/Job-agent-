#!/usr/bin/env python3
"""Fetch open job listings from Workable-hosted company job boards."""

import time

import requests

# EDETEK is a real eClinical/clinical-data CRO with multiple Brazil/LATAM
# postings (Clinical Data Manager, Senior Clinical Project Manager, Senior
# Clinical QA Specialist, etc.) as of this check.
COMPANIES = {
    "edetek": "EDETEK",
}

WORKABLE_URL_TEMPLATE = "https://apply.workable.com/api/v1/widget/accounts/{account}?details=true"

# Workable's endpoint 429s without a browser-like User-Agent, and
# occasionally even with one -- worth a couple of retries.
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def fetch_jobs(account, retries=3, backoff_seconds=5):
    url = WORKABLE_URL_TEMPLATE.format(account=account)
    for attempt in range(retries):
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 429 and attempt < retries - 1:
            time.sleep(backoff_seconds * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json().get("jobs", [])
    return []


def normalize_location(job):
    country = job.get("country", "")
    city = job.get("city", "")
    parts = [p for p in (city, country) if p]
    location = ", ".join(parts)
    return f"Remote, {location}" if job.get("telecommuting") else location


def main():
    for account, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            jobs = fetch_jobs(account)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue

        print(f"{len(jobs)} open jobs\n")
        for job in jobs:
            print(job["title"])
            print(job["url"])
            print()


if __name__ == "__main__":
    main()
