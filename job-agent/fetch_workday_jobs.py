#!/usr/bin/env python3
"""Fetch open job listings from Workday-hosted career sites -- originally
built for major CROs missing from the other providers in this pipeline
(Greenhouse/Lever/Workable/SmartRecruiters/Ashby/Gupy), later extended to
large non-pharma employers for the capacity-based (industry-agnostic)
search: large multi-country program management, executive/named-client
relationship ownership, bid/proposal leadership, or 50+ person distributed
team oversight, regardless of sector.

Workday exposes a public, unauthenticated JSON search API per tenant at
https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs (POST),
and a matching per-job detail endpoint at .../job{externalPath} (GET) --
the same data any visitor's browser receives, no auth required. Verified
directly (see README) before committing to this provider.

Pharma/CRO tenants (checked first): IQVIA, Parexel, Syneos Health, ICON
plc, Fortrea confirmed on Workday. Medpace uses iCIMS
(uscareers-medpace.icims.com); PPD (Thermo Fisher's clinical-research
business) uses Phenom People (jobs.thermofisher.com) -- neither is on
Workday, so neither is covered by any provider in this pipeline.

Non-pharma tenants (added for the capacity-based search): Accenture and
Kyndryl (IBM's IT-infrastructure-services spinoff) confirmed on Workday
with real São Paulo/Rio-based Director/Associate-Director/bid-leadership
roles. Checked and NOT confirmed on any of this pipeline's supported ATS
platforms (Greenhouse/Lever/Workable/SmartRecruiters/Ashby/Workday):
Globant, EPAM Systems, Endava, Capgemini, DXC Technology, NTT Data,
Cognizant, Wipro, Infosys, TCS, IBM, AECOM, Jacobs, WSP, Fluor, Bechtel --
most run custom/proprietary career portals with no public API discovered.
TELUS Digital Brazil has a Greenhouse board (telusdigitalbr) but no live
postings as of this check. Thoughtworks is on Greenhouse (confirmed, 46
jobs) but none are Brazil-eligible/senior enough as of this check --
listed here for the record even though it isn't added to COMPANIES below,
since Greenhouse doesn't need a fetch_workday_jobs.py entry.

Each tenant's facet configuration differs (IQVIA exposes a
Location_Country facet; most others don't), so rather than depend on
facets this searches Workday's full-text `searchText` per tenant (see
`search_terms` per entry in _TENANTS, falling back to DEFAULT_SEARCH_TERMS
if unset), merging results across terms (deduped by externalPath). Pharma
CRO boards run 300-1,800+ total postings; Accenture/Kyndryl run into the
thousands across every function and seniority level, so their search
terms combine a location signal with a seniority/capacity signal (e.g.
"Sao Paulo Director") rather than relying on location alone -- fetching
everything and filtering client-side, as the smaller providers do, isn't
practical at this scale.
"""

import requests

COMPANIES = {
    "iqvia": "IQVIA",
    "parexel": "Parexel",
    "syneoshealth": "Syneos Health",
    "icon": "ICON plc",
    "fortrea": "Fortrea",
    "accenture": "Accenture",
    "kyndryl": "Kyndryl",
}

DEFAULT_SEARCH_TERMS = ("Brazil", "LATAM")

_TENANTS = {
    "iqvia": {"host": "iqvia.wd1", "tenant": "iqvia", "site": "IQVIA"},
    "parexel": {"host": "parexel.wd1", "tenant": "parexel", "site": "Parexel_External_Careers"},
    "syneoshealth": {
        "host": "syneoshealth.wd12", "tenant": "syneoshealth", "site": "Syneos_Health_External_Site",
    },
    "icon": {"host": "icon.wd3", "tenant": "icon", "site": "broadbean_external"},
    "fortrea": {"host": "fortrea.wd1", "tenant": "fortrea", "site": "Fortrea"},
    "accenture": {
        "host": "accenture.wd103", "tenant": "accenture", "site": "AccentureCareers",
        "search_terms": (
            "Sao Paulo Director", "Sao Paulo Associate Director", "Sao Paulo Program Manager",
            "Brazil Bid Manager", "Propostas Comerciais", "Sao Paulo Senior Manager",
        ),
    },
    "kyndryl": {
        "host": "kyndryl.wd5", "tenant": "kyndryl", "site": "KyndrylProfessionalCareers",
        "search_terms": (
            "Brazil Program Director", "Brazil Delivery Manager", "Brazil Client Executive",
            "Sao Paulo Customer Unit Leader", "Sao Paulo Customer Partner",
        ),
    },
}

# Confirmed NOT on Workday during this search -- kept as a record so
# these don't get re-guessed as Workday tenants on a future pass.
NOT_ON_WORKDAY = {
    "Medpace": "iCIMS (uscareers-medpace.icims.com)",
    "PPD / Thermo Fisher Scientific": "Phenom People (jobs.thermofisher.com)",
}

# Checked for a public ATS API on any provider this pipeline supports and
# NOT found -- most run custom/proprietary career portals. Kept as a
# record so these aren't re-guessed on a future search pass.
NO_PUBLIC_API_FOUND = (
    "Globant", "EPAM Systems", "Endava", "Capgemini", "DXC Technology", "NTT Data",
    "Cognizant", "Wipro", "Infosys", "TCS (Tata Consultancy Services)", "IBM",
    "AECOM", "Jacobs Engineering", "WSP Global", "Fluor", "Bechtel",
)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
PAGE_SIZE = 20


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
    """Merged, deduped (by externalPath) results across this tenant's
    search terms (per-tenant `search_terms` in _TENANTS if set, else
    DEFAULT_SEARCH_TERMS)."""
    terms = _TENANTS[company_key].get("search_terms", DEFAULT_SEARCH_TERMS)
    seen = {}
    for term in terms:
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
