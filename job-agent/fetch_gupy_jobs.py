#!/usr/bin/env python3
"""Fetch open job listings from Gupy-hosted company job boards -- Brazil's
dominant recruiting platform, used by genuinely Brazilian-market employers
(as opposed to the international/foreign-HQ companies on the other five
providers, which reach into Brazil via remote/PEO arrangements).

Gupy has no documented public read API (developers.gupy.io covers the
authenticated employer-side API only). Company career pages
(https://{company}.gupy.io/) are public and server-render the full open
job list into a Next.js __NEXT_DATA__ script tag -- this is the same
data any visitor's browser receives unauthenticated, so reading it here
follows the same principle as the other providers' public JSON APIs.

COMPANIES covers every confirmed genuinely Brazilian-market employer on
Gupy checked so far -- both the clinical operations/trial management
companies from the original search and the major Brazilian pharma
companies added for the Director/Country Manager "stretch/leadership"
search (see README's "Stretch/leadership search" section). Not every
company here currently has clinical-ops-relevant or leadership-level
postings open; that's expected and reassessed at scoring time each run,
not filtered out here.
"""

import json
import re

import requests

COMPANIES = {
    "synvia": "Synvia",  # dedicated Brazilian CRO -- largest, most relevant clinical-ops hit
    "idor": "IDOR",  # Instituto D'Or de Pesquisa e Ensino (Rede D'Or's research institute)
    "eurofarma": "Eurofarma",  # major Brazilian pharma
    "rennova": "Rennova",  # aesthetics/medical products co. with a clinical research function
    "vagasache": "Aché",  # major Brazilian pharma, added for the leadership/stretch search
    "hyperapharma": "Hypera Pharma",  # major Brazilian pharma, added for the leadership/stretch search
}

# EMS Farmacêutica: could NOT confirm a working Gupy subdomain. "ems" is a
# genuine Gupy-hosted 404 (not a DNS failure), and several plausible
# alternates (emsfarmaceutica, gruponc, vagasems, etc.) also 404. Multiple
# secondary sources claim ems.gupy.io is correct, so this may be a
# recently deactivated/migrated board rather than never-existed -- worth
# re-checking on a future search rather than treating as permanently ruled
# out.

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def fetch_jobs(subdomain):
    response = requests.get(f"https://{subdomain}.gupy.io/", headers=HEADERS, timeout=30)
    response.raise_for_status()
    match = _NEXT_DATA_RE.search(response.text)
    if not match:
        return []
    data = json.loads(match.group(1))
    return data["props"]["pageProps"].get("jobs", [])


def normalize_location(job):
    address = job["workplace"]["address"]
    city, state = address.get("city"), address.get("stateShortName")
    place = f"{city}, {state}" if city and state else (city or "")
    workplace_type = job["workplace"].get("workplaceType", "")
    label = {"remote": "Remote", "hybrid": "Hybrid", "on-site": "On-site"}.get(workplace_type, "")
    if place and label:
        return f"{label}, {place}"
    return place or label


def job_url(subdomain, job_id):
    return f"https://{subdomain}.gupy.io/jobs/{job_id}"


def fetch_job_detail(subdomain, job_id):
    """Fetch the job detail page (same __NEXT_DATA__ mechanism as the
    listing page) for description/prerequisites/responsibilities text --
    not present on the list-page job objects."""
    response = requests.get(job_url(subdomain, job_id), headers=HEADERS, timeout=30)
    response.raise_for_status()
    match = _NEXT_DATA_RE.search(response.text)
    if not match:
        return {}
    data = json.loads(match.group(1))
    return data["props"]["pageProps"].get("job", {})


def main():
    for subdomain, company_name in COMPANIES.items():
        print(f"=== {company_name} ===")
        try:
            jobs = fetch_jobs(subdomain)
        except requests.exceptions.RequestException as exc:
            print(f"  Failed to fetch listings: {exc}\n")
            continue

        print(f"{len(jobs)} open jobs\n")
        for job in jobs:
            print(job["title"])
            print(job_url(subdomain, job["id"]))
            print()


if __name__ == "__main__":
    main()
