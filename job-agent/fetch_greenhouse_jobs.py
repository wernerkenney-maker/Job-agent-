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
    "precisionaq": "Precision AQ",
    "clinchoice": "ClinChoice",
}

# Companies that are separate Greenhouse boards but the same corporate
# family, so identical roles get posted to more than one board. Used to
# dedupe sibling postings into a single match with multiple apply links.
COMPANY_FAMILIES = {
    "Precision Medicine Group": "Precision Medicine Group family",
    "Precision for Medicine": "Precision Medicine Group family",
    "Precision AQ": "Precision Medicine Group family",
}

GREENHOUSE_URL_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
GREENHOUSE_JOB_DETAIL_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}?content=true"


def fetch_jobs(board_token):
    url = GREENHOUSE_URL_TEMPLATE.format(token=board_token)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json().get("jobs", [])


def fetch_job_detail(board_token, job_id):
    """Fetch a single job's full detail, including description content and
    any pay-transparency metadata, used for salary extraction."""
    url = GREENHOUSE_JOB_DETAIL_TEMPLATE.format(token=board_token, job_id=job_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


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
