#!/usr/bin/env python3
"""Fetch open job listings from SmartRecruiters-hosted company job boards."""

import requests

# PSI CRO is a well-established (founded 1995, 3,000+ employees), privately
# held global CRO with multiple Brazil-based postings (Clinical Regional
# Project Lead, Therapeutic Area Lead, Lead CRA, Data Manager for Clinical
# Trials, etc.) as of this check.
COMPANIES = {
    "PSICRO": "PSI CRO",
}

POSTINGS_URL_TEMPLATE = "https://api.smartrecruiters.com/v1/companies/{company_id}/postings"
POSTING_DETAIL_URL_TEMPLATE = "https://api.smartrecruiters.com/v1/companies/{company_id}/postings/{posting_id}"
# The list endpoint doesn't include a posting URL; this bare form (no slug
# suffix) resolves fine without an extra request per job.
POSTING_URL_TEMPLATE = "https://jobs.smartrecruiters.com/{company_id}/{posting_id}"


def fetch_jobs(company_id):
    postings = []
    offset = 0
    while True:
        url = POSTINGS_URL_TEMPLATE.format(company_id=company_id)
        response = requests.get(url, params={"limit": 100, "offset": offset}, timeout=30)
        response.raise_for_status()
        data = response.json()
        page = data.get("content", [])
        postings.extend(page)
        if len(page) < 100:
            break
        offset += 100
    return postings


def fetch_job_detail(company_id, posting_id):
    url = POSTING_DETAIL_URL_TEMPLATE.format(company_id=company_id, posting_id=posting_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    for company_id, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            postings = fetch_jobs(company_id)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue

        print(f"{len(postings)} open jobs\n")
        for posting in postings:
            print(posting["name"])
            print(POSTING_URL_TEMPLATE.format(company_id=company_id, posting_id=posting["id"]))
            print()


if __name__ == "__main__":
    main()
