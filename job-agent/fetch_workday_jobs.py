#!/usr/bin/env python3
"""Fetch open job listings from Workday-hosted career sites for major
CROs that have no presence on any of the other providers in this
pipeline (Greenhouse/Lever/Workable/SmartRecruiters/Ashby/Gupy).

Workday exposes a public, unauthenticated JSON search API per tenant at
https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs (POST),
and a matching per-job detail endpoint at .../job{externalPath} (GET) --
the same data any visitor's browser receives, no auth required. Verified
directly (see README) before committing to this provider.

Checked all seven major CROs missing from the other providers:
- IQVIA, Parexel, Syneos Health, ICON plc, Fortrea -- confirmed on
  Workday, tenant/site config in _TENANTS below.
- Medpace -- NOT on Workday; uses iCIMS (uscareers-medpace.icims.com).
  A dedicated iCIMS module would be needed to cover it; out of scope
  for this provider.
- PPD (the clinical-research business of Thermo Fisher Scientific) --
  NOT on Workday; uses Phenom People (jobs.thermofisher.com), same
  platform already noted as a dead end for standalone Thermo Fisher in
  README.md.

Each tenant's facet configuration differs (IQVIA exposes a
Location_Country facet; Parexel/Syneos/ICON/Fortrea don't), so rather
than depend on facets this searches Workday's full-text `searchText`
for "Brazil" and separately for "LATAM", merging the results (deduped
by externalPath) -- catches both Brazil-specific postings and broader
LATAM-inclusive-remote roles that don't mention Brazil by name in the
title/summary. These boards run to 300-1,800+ total postings, far too
many to fetch in full, so this search-side narrowing (rather than
fetch-everything-then-filter, as the smaller providers do) is what
keeps this practical.
"""

import requests

COMPANIES = {
    "iqvia": "IQVIA",
    "parexel": "Parexel",
    "syneoshealth": "Syneos Health",
    "icon": "ICON plc",
    "fortrea": "Fortrea",
}

_TENANTS = {
    "iqvia": {"host": "iqvia.wd1", "tenant": "iqvia", "site": "IQVIA"},
    "parexel": {"host": "parexel.wd1", "tenant": "parexel", "site": "Parexel_External_Careers"},
    "syneoshealth": {
        "host": "syneoshealth.wd12", "tenant": "syneoshealth", "site": "Syneos_Health_External_Site",
    },
    "icon": {"host": "icon.wd3", "tenant": "icon", "site": "broadbean_external"},
    "fortrea": {"host": "fortrea.wd1", "tenant": "fortrea", "site": "Fortrea"},
}

# Confirmed NOT on Workday during this search -- kept as a record so
# these don't get re-guessed as Workday tenants on a future pass.
NOT_ON_WORKDAY = {
    "Medpace": "iCIMS (uscareers-medpace.icims.com)",
    "PPD / Thermo Fisher Scientific": "Phenom People (jobs.thermofisher.com)",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
PAGE_SIZE = 20
SEARCH_TERMS = ("Brazil", "LATAM")


def _search(company_key, search_text):
    config = _TENANTS[company_key]
    url = f"https://{config['host']}.myworkdayjobs.com/wday/cxs/{config['tenant']}/{config['site']}/jobs"
    results = []
    offset = 0
    while True:
        response = requests.post(
            url,
            headers=HEADERS,
            timeout=30,
            json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": search_text},
        )
        response.raise_for_status()
        data = response.json()
        postings = data.get("jobPostings", [])
        results.extend(postings)
        offset += PAGE_SIZE
        if not postings or offset >= data.get("total", 0):
            break
    return results


def fetch_jobs(company_key):
    """Merged, deduped (by externalPath) results across SEARCH_TERMS."""
    seen = {}
    for term in SEARCH_TERMS:
        for posting in _search(company_key, term):
            seen[posting["externalPath"]] = posting
    return list(seen.values())


def job_url(company_key, external_path):
    config = _TENANTS[company_key]
    return f"https://{config['host']}.myworkdayjobs.com/{config['site']}{external_path}"


def fetch_job_detail(company_key, external_path):
    config = _TENANTS[company_key]
    url = f"https://{config['host']}.myworkdayjobs.com/wday/cxs/{config['tenant']}/{config['site']}{external_path}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json().get("jobPostingInfo", {})


def main():
    for company_key, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            jobs = fetch_jobs(company_key)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue
        print(f"{len(jobs)} Brazil/LATAM-matched jobs\n")
        for job in jobs:
            print(job["title"], "|", job.get("locationsText", ""))
            print(job_url(company_key, job["externalPath"]))
            print()

    if NOT_ON_WORKDAY:
        print("=== Not on Workday (confirmed) ===")
        for name, platform in NOT_ON_WORKDAY.items():
            print(f"{name}: {platform}")


if __name__ == "__main__":
    main()
