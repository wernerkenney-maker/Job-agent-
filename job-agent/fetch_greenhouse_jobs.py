#!/usr/bin/env python3
"""Fetch open job listings from several companies' Greenhouse job boards and
print them grouped by company.

Note: Thermo Fisher's careers site (jobs.thermofisher.com) is built on Phenom
People, not Greenhouse, so no boards-api.greenhouse.io/v1/boards/thermofisher
endpoint exists. The companies below are real Greenhouse-hosted CROs and
biotechs known to hire remote clinical operations / clinical trial
management roles, several with listings explicitly open to Brazil/LATAM.
"""

import requests

# Greenhouse board tokens for CROs/biotechs that commonly hire remote
# clinical operations / trial management roles open to LATAM/Brazil.
COMPANIES = {
    "iovancebiotherapeutics": "Iovance Biotherapeutics",
    "precisionmedicinegroup": "Precision Medicine Group",
    "pfm": "Precision for Medicine",
    "clinchoice": "ClinChoice",
}

GREENHOUSE_URL_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


def fetch_jobs(board_token):
    url = GREENHOUSE_URL_TEMPLATE.format(token=board_token)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json().get("jobs", [])


def main():
    for board_token, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            jobs = fetch_jobs(board_token)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue

        print(f"{len(jobs)} open jobs\n")
        for job in jobs:
            print(job["title"])
            print(job["absolute_url"])
            print()


if __name__ == "__main__":
    main()
