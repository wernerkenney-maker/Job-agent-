#!/usr/bin/env python3
"""Fetch open job listings from Lever-hosted company job boards, alongside
the Greenhouse boards in fetch_greenhouse_jobs.py.

Company search notes (see README for the full writeup): most Lever
postings claiming to be "CRO"/clinical roles turned out to be from
Jobgether, a third-party AI-matching recruiting layer that reposts other
companies' jobs and routes applications through its own screening rather
than straight to the employer -- excluded, not a real CRO/biotech/pharma
company. Welo Global was also excluded -- despite a "Life Sciences"
business line, its actual Brazil-tagged openings are generic data-
annotation/BPO gig work (e.g. "Ads Quality Rater"), not clinical roles.
"""

import requests

# Lever company slugs. Alimentiv is a genuine mid-size CRO (GI/inflammation
# focus) with broad international remote hiring (Europe, Africa, India,
# Canada, US) and historical evidence of LATAM-scoped postings, though none
# are live as of this check -- tracked so future LATAM/Brazil postings get
# caught automatically.
COMPANIES = {
    "alimentiv-2": "Alimentiv",
}

LEVER_URL_TEMPLATE = "https://api.lever.co/v0/postings/{token}?mode=json"


def fetch_jobs(company_token):
    url = LEVER_URL_TEMPLATE.format(token=company_token)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def normalize_location(posting):
    locations = posting.get("categories", {}).get("allLocations") or []
    if not locations:
        loc = posting.get("categories", {}).get("location")
        locations = [loc] if loc else []
    prefix = "Remote, " if posting.get("workplaceType") == "remote" else ""
    return prefix + "; ".join(locations) if locations else ""


def main():
    for token, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            postings = fetch_jobs(token)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue

        print(f"{len(postings)} open jobs\n")
        for posting in postings:
            print(posting["text"])
            print(posting["hostedUrl"])
            print()


if __name__ == "__main__":
    main()
