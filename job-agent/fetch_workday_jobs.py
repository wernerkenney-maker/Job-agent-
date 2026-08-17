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

Pharma/CRO tenants confirmed on Workday: IQVIA, Parexel, Syneos Health,
ICON plc, Fortrea, and Thermo Fisher Scientific (a *separate* Workday
tenant -- thermofisher.wd5/thermofisher/thermofishercareers -- from the
Phenom-People-hosted jobs.thermofisher.com main careers site; both exist
in parallel, confirmed directly by probing the CXS API and cross-checking
against a live search hit). Medpace uses iCIMS
(uscareers-medpace.icims.com) -- not on Workday, not covered by any
provider in this pipeline.

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

FETCH STRATEGY -- full catalog, not keyword search, for pharma/CRO
tenants:

Workday's full-text `searchText` matching is unreliable for this
purpose -- confirmed directly against IQVIA's own API: searching "Brazil"
or "LATAM" does NOT return "Site Activation Manager (Global)" or "Assoc.
Site Activation Manager - Sponsor Dedicated", despite São Paulo, Brazil
being each posting's *primary* listed location. Relying on searchText
silently drops genuinely Brazil-eligible postings whose title doesn't
happen to contain a matched term. So pharma/CRO tenants are fetched via
a blank search (searchText="") -- Workday's full, paginated catalog --
title/location only, cheap. Non-pharma tenants (Accenture, Kyndryl) keep
the narrower `search_terms`-based strategy: their catalogs run into the
thousands across every function and seniority level, so fetching
everything and filtering client-side isn't practical at that scale (see
`search_terms` per entry in _TENANTS).

Separately, Workday collapses a posting with more than one office into a
`locationsText` summary like "4 Locations" -- hiding which countries are
actually included. Confirmed directly: IQVIA's "Site Activation Manager
(Global)" (São Paulo, Brazil is the primary location) and Fortrea's
"Senior Site Navigator" (São Paulo/Remote Brazil) both show only as "N
Locations" in the catalog list -- a location-text filter looking for the
literal word "Brazil" would silently miss both. `_resolve_ambiguous_locations()`
fetches job detail only for postings whose locationsText collapses like
this (not the full catalog), replacing it with the real semicolon-joined
location list, so downstream Brazil-eligibility filtering can actually
see them. This is inherently client-side/local work -- Workday's search
API gives no way to filter by "any of N locations is Brazil" server-side.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

COMPANIES = {
    "iqvia": "IQVIA",
    "parexel": "Parexel",
    "syneoshealth": "Syneos Health",
    "icon": "ICON plc",
    "fortrea": "Fortrea",
    "thermofisher": "Thermo Fisher Scientific",
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
    "thermofisher": {"host": "thermofisher.wd5", "tenant": "thermofisher", "site": "thermofishercareers"},
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
    """Paginate through every result for one search. Workday's `total`
    field is only reliable on the first page -- confirmed directly: it
    flakily reports 0 on later pages of the same search even with
    thousands of real postings remaining, which would terminate
    pagination after just one page if re-read each time. So `total` is
    captured once, from the first response, and reused for every
    subsequent page's termination check. Also confirmed: Workday silently
    fails (empty results, `total: None`) for any `limit` above 20, so
    PAGE_SIZE must stay at the API's actual cap."""
    config = _TENANTS[company_key]
    url = f"https://{config['host']}.myworkdayjobs.com/wday/cxs/{config['tenant']}/{config['site']}/jobs"
    results = []
    offset = 0
    total = None
    while True:
        response = requests.post(
            url,
            headers=HEADERS,
            timeout=30,
            json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": search_text},
        )
        response.raise_for_status()
        data = response.json()
        if total is None:
            total = data.get("total") or 0
        postings = data.get("jobPostings", [])
        results.extend(postings)
        offset += PAGE_SIZE
        if not postings or offset >= total:
            break
    return results


RESOLVE_WORKERS = 12


def _resolve_ambiguous_locations(company_key, postings):
    """Mutates each posting whose locationsText is an "N Locations"
    summary, replacing it with the real semicolon-joined location list
    fetched from job detail. See module docstring for why this is
    necessary -- a summary like "4 Locations" can and does include
    Brazil while giving no client-side way to tell without this.

    Fetched concurrently (RESOLVE_WORKERS at a time): a large pharma/CRO
    catalog can have hundreds of ambiguous multi-location postings, and
    resolving them one at a time made a single tenant's fetch take up to
    15 minutes (confirmed directly: IQVIA's full fetch went from ~125s
    for the raw listing to 897s once every ambiguous posting was resolved
    sequentially). A thread pool cuts that to the cost of the slowest
    individual request rather than the sum of all of them, since these
    are small, independent GET requests with no shared state."""
    ambiguous = [p for p in postings if "Locations" in (p.get("locationsText") or "")]
    if not ambiguous:
        return

    def resolve_one(posting):
        try:
            detail = fetch_job_detail(company_key, posting["externalPath"])
        except requests.exceptions.RequestException:
            return
        primary = detail.get("location") or ""
        additional = detail.get("additionalLocations") or []
        all_locations = [loc for loc in [primary, *additional] if loc]
        if all_locations:
            posting["locationsText"] = "; ".join(all_locations)

    with ThreadPoolExecutor(max_workers=RESOLVE_WORKERS) as pool:
        futures = [pool.submit(resolve_one, posting) for posting in ambiguous]
        for future in as_completed(futures):
            future.result()  # surface any unexpected (non-request) exception


def fetch_jobs(company_key):
    """Pharma/CRO tenants: full catalog (blank search), then resolve any
    ambiguous multi-location summaries. Non-pharma tenants (whose config
    sets `search_terms`): the narrower keyword-search strategy, merged
    and deduped by externalPath across search terms -- catalogs run into
    the thousands across every function, so a full-catalog fetch isn't
    practical at that scale."""
    config = _TENANTS[company_key]
    if "search_terms" in config:
        seen = {}
        for term in config["search_terms"]:
            for posting in _search(company_key, term):
                seen[posting["externalPath"]] = posting
        postings = list(seen.values())
    else:
        postings = _search(company_key, "")
    _resolve_ambiguous_locations(company_key, postings)
    return postings


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
        print(f"{len(jobs)} jobs\n")
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
