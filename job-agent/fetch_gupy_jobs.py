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
"""

import json
import re

import requests

# All confirmed genuinely Brazilian-market employers (not international
# remote) with clinical operations/trial management-relevant postings:
COMPANIES = {
    "synvia": "Synvia",  # dedicated Brazilian CRO -- largest, most relevant hit
    "idor": "IDOR",  # Instituto D'Or de Pesquisa e Ensino (Rede D'Or's research institute)
    "eurofarma": "Eurofarma",  # major Brazilian pharma
    "rennova": "Rennova",  # aesthetics/medical products co. with a clinical research function
}

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
