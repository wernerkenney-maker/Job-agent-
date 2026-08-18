#!/usr/bin/env python3
"""Fetch jobs from the configured Greenhouse, Lever, Workable,
SmartRecruiters, Ashby, Gupy (Brazilian-market), and Workday boards,
score each one for fit against a candidate's background using Claude,
dedupe sibling postings, track which matches are new since the last run,
draft cover letters + tailored resume bullets for 80+ scores, estimate
salary where undisclosed, and refresh report.html.

Requires an Anthropic API key in the ANTHROPIC_API_KEY environment variable.
"""

import html
import json
import os
import re
import sys

import anthropic

import fetch_ashby_jobs
import fetch_greenhouse_jobs
import fetch_gupy_jobs
import fetch_lever_jobs
import fetch_smartrecruiters_jobs
import fetch_workable_jobs
import fetch_workday_jobs
from br_salary_estimate import estimate_br_salary
from cover_letter import generate_cover_letter_via_claude, save_cover_letter
from pipeline import MIN_SCORE, check_expired_links, process_run
from relocation import detect_relocation_support
from report import write_report
from resume_bullets import generate_resume_bullets_via_claude, save_resume_bullets
from salary import (
    extract_salary,
    extract_salary_ashby,
    extract_salary_lever,
    extract_salary_smartrecruiters,
    extract_salary_workable,
    extract_salary_workday,
)
from salary_estimate import estimate_salary_via_claude

CANDIDATE_PROFILE = """
Portfolio Manager at Labcorp Clinical Laboratory Services (Labcorp CLS),
overseeing 100+ global clinical studies and $200M+ in annual revenue.
Serves as an escalation point supporting a team of 100+ project managers
globally, and personally leads the most complex "giga trials" on the
portfolio. Global Study Manager on HORIZON, the largest trial Novartis
runs with Labcorp -- representing Labcorp internationally to Novartis
in person (London, Basel, and London again), regularly participates in
client audits, represents Labcorp directly to Novartis's operational
group, and has participated in 4 bid defenses -- real client-facing and
commercial credibility, not just internal operational scope. Previously
Global Clinical Study Manager, managing $20M+ trial budgets across
Oncology, Autoimmune, and Malaria trials. Before that, Regional Study
Coordinator, EMEA. Certificate in Project Management from Rutgers.
Trilingual: English (C2), Portuguese (C2), German (B1). 5.5 years of
progressively senior experience, on a fast trajectory but not yet
holding a prior Director-level title. Based in Fortaleza, Brazil.
""".strip()

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
BATCH_SIZE = 40
DESCRIPTION_EXCERPT_LENGTH = 1500

# The one legitimate pre-scoring filter: geography, not title. The
# candidate genuinely cannot work a Beijing-only or US-only role
# regardless of what its responsibilities are, so this is checked before
# spending a detail fetch. A title-based filter, by contrast, was
# silently dropping real matches at already-integrated companies --
# "Site Activation Manager" (IQVIA) and "Senior Site Navigator" (Fortrea)
# are both genuinely Brazil-eligible but don't contain any of the
# "manager/director/coordinator" keyword-style signal a title filter
# would look for, and Workday's own full-text "Brazil"/"LATAM" search
# doesn't reliably surface them either (confirmed directly against
# IQVIA's API). So every location-eligible posting gets its full
# description fetched and scored on actual content -- title is a label
# on the result, never a gate before scoring.
# Location strings are NOT normalized across providers, so matching on the
# English word "Brazil" alone silently loses whole employers. Confirmed
# formats actually seen in live data: "São Paulo, Brazil" (IQVIA),
# "Remote, Brazil" (Thermo Fisher), "Brazil-Remote"/"Brazil-Sao Paulo"
# (Parexel), "Brazil, Sao Paulo" (ICON), and -- the one that bites --
# ISO-3166 alpha-3 codes with no country name at all: "BRA-Remote",
# "BRA-Client" (Syneos Health). A "brazil|brasil" pattern drops every
# Syneos Brazil posting (14 live as of this check, including genuine
# CTM-level matches). Any new provider must be checked against this list
# before being trusted -- a location filter that misses a format fails
# exactly like the title filter it replaced: silently, with no error.
_BRAZIL_LOCATION_RE = re.compile(
    r"brazil|brasil|\bbra\s*-|\bbra\b|s[aã]o paulo|sao paulo|fortaleza|bras[ií]lia|"
    r"rio de janeiro|curitiba|hortol[aâ]ndia|campinas|paul[ií]nia|latam|latin america",
    re.I,
)


def _is_location_eligible(job):
    """True if this posting's location is Brazil/LATAM-explicit, or bare/
    ambiguous ("Remote" with no country named, or no location text at
    all) -- worth a description fetch to resolve. False only when the
    location explicitly names a different, specific country/region with
    no Brazil/LATAM mention (e.g. "Beijing, China", "Remote, United
    States") -- fetching those would be pure waste, since no description
    changes their geography. Gupy postings are always eligible: the
    market is Brazilian by definition (see fetch_gupy_jobs.py)."""
    if job.get("market") == "Brazilian market (local)":
        return True
    location = (job.get("location") or "").strip()
    if not location or location.lower() == "remote":
        return True
    return bool(_BRAZIL_LOCATION_RE.search(location))


def _strip_html_to_text(raw):
    text = html.unescape(raw or "")
    text = re.sub(r"<[^<]+?>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

SCORING_INSTRUCTIONS = """
You are screening job listings for fit against a candidate's background.

Candidate background:
{profile}

The candidate is not limited to their exact current title or to pharma/
CRO employers. Score roles in two overlapping lanes:
1. Pharma/biotech: clinical operations, quality, regulatory affairs,
   medical affairs, or other pharma/biotech leadership functions where
   their trial/portfolio management experience is a strong transferable
   fit.
2. ANY other industry, on a capacity basis: large, complex, multi-country
   program management ($100M+ scope), executive/named-client relationship
   ownership, bid or proposal leadership, or oversight of 50+ person
   distributed teams. The function/industry doesn't need to resemble
   pharma at all -- what matters is that the role's actual demands
   (program scale, client-facing seniority, distributed team leadership)
   match what the candidate already does, regardless of sector.

Prioritize compensation and long-term career trajectory over an exact
title match: a role in an adjacent function or industry at
equal-or-better seniority, pay, and growth potential should score as
well as or better than a narrower title match at a lower level (e.g. a
"Consultant" or "Associate"-level contract role should score lower than
a permanent managerial role, even in a closer-sounding function).

Each job below includes an excerpt of its actual description --
responsibilities and requirements. Score from that content, not from the
title. A title alone is not sufficient signal either way: an
unfamiliar-sounding or generic title ("Site Activation Manager," "Senior
Site Navigator," "Clinical Team Lead") can carry real manager-level
program/site-leadership scope that only the description reveals, exactly
as easily as an impressive-sounding title can turn out to be individual-
contributor work once you read what it actually does. Read the excerpt
and judge real scope, seniority, and functional fit from it every time --
never pattern-match on the title string itself.

Hard requirements, not traded off:
- Workable from Brazil -- either explicitly remote/LATAM-inclusive, OR
  physically located on-site/hybrid within Brazil (any city; the
  candidate is based in Fortaleza but open to relocating for the right
  on-site/hybrid role). If neither is true, score no higher than 40
  regardless of how strong the functional fit is.
- Manager-level or above ONLY. Never surface individual-contributor,
  analyst, associate, or coordinator-level roles, even if the function
  is a strong fit -- score these no higher than 30 regardless of
  functional fit. (A role titled "Coordenador"/"Coordinator" that
  genuinely carries site/team leadership scope, not just individual
  task execution, is the one borderline exception -- judge by real
  scope, not the bare word.)

Level calibration -- this is the candidate's actual level, not aspiration:
5.5 years of progressively senior experience, fast trajectory, but no
prior Director-level title. Senior Manager, Associate Director, and
Regional Director (or equivalent titles/scope in non-pharma industries)
are the PRIMARY realistic target level -- score these on their merits
using the normal 1-100 scale. Full Director, VP, Country Manager, or
higher (or equivalent scope) are a genuine reach: still score them
honestly on fit, but set level: "Reach" for these regardless of score,
and lean toward "Long-shot" probability unless the specific posting's
own requirements (not just title) plausibly match 5.5 years of
experience -- don't inflate probability just because the fit narrative
sounds good.

For Director/Country Manager-level and other client-facing or
business-development-adjacent roles specifically (whether "Reach" or
not), weigh the candidate's sponsor-facing and commercial credibility
explicitly: representing Labcorp internationally to a major sponsor
(Novartis), regular client audit participation, and bid-defense
experience are exactly what these roles screen for, distinct from (and
beyond) pure operational/trial-management scope -- don't undercount this
dimension for those role types.

The candidate is trilingual (English C2, Portuguese C2, German B1).
Factor this in specifically -- beyond the baseline Brazil-eligibility
requirement -- for roles that explicitly span EMEA/LATAM or explicitly
value multilingual client-facing work; it's a genuine differentiator
there, not just a generic nice-to-have.

For each job below, also determine:
- category: "In-field" if it's direct clinical operations / clinical
  trial management work, or "Adjacent" if it's a transferable-skills fit
  elsewhere (regulatory, quality, program/portfolio leadership outside
  pharma -- including non-pharma industries scored under lane 2 above).
- level: "Primary" for Senior Manager/Associate Director/Regional
  Director-equivalent scope, or "Reach" for Director/VP/Country
  Manager-equivalent scope or higher.
- probability: a realistic "High", "Medium", or "Long-shot" assessment of
  the candidate's odds, based on how closely their actual experience maps
  to what the role likely requires (seniority, domain depth, therapeutic
  area, language/region fit) -- be honest, not encouraging by default.
- trajectory: one line (under 20 words) on whether this would be a
  lateral move, a step up, or a bigger leap versus the candidate's current
  Portfolio Manager role, and a plain-spoken note on whether it's worth
  pursuing even if it's a stretch.

For each job below, score fit from 1 (no fit) to 100 (excellent fit). Each
job has a batch-local numeric id (0, 1, 2, ...) -- echo that same integer
back, not any id/UUID mentioned in the job's own text.

Jobs:
{jobs}

Respond with ONLY a JSON array, no other text, in this exact form:
[{{"id": <batch-local integer id>, "score": <integer 1-100>, "reason": "<one-line reason, under 20 words>", "category": "In-field|Adjacent", "level": "Primary|Reach", "probability": "High|Medium|Long-shot", "trajectory": "<one-line note, under 20 words>"}}, ...]
Include exactly one entry per job listed above, in any order.
"""


def _collect_provider(all_jobs, company_name, fetch, mapper):
    """Fetch one company's postings and map them into the common shape.

    Both stages are isolated. A fetch failure skips that company, as
    before. A *mapping* failure now skips only the offending posting:
    previously the per-posting loop sat outside the try, so a single
    malformed record -- a Workday entry with no externalPath, seen in
    live full-catalog data -- raised straight out of collect_all_jobs()
    and discarded every provider already fetched. With Workday now
    pulling full catalogs, that meant losing a ten-minute fetch to one
    bad row. Skipped postings are counted and reported rather than
    passed over in silence."""
    try:
        postings = fetch()
    except Exception as exc:
        print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
        return

    skipped = 0
    for posting in postings:
        try:
            mapped = mapper(posting)
        except Exception as exc:
            skipped += 1
            if skipped == 1:  # report the first one concretely, then just count
                print(f"  {company_name}: skipping malformed posting ({exc!r})", file=sys.stderr)
            continue
        if mapped is not None:
            all_jobs.append(mapped)
    if skipped:
        print(f"  {company_name}: skipped {skipped} malformed posting(s)", file=sys.stderr)


def collect_all_jobs():
    all_jobs = []

    for board_token, company_name in fetch_greenhouse_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda t=board_token: fetch_greenhouse_jobs.fetch_jobs(t),
            lambda job, t=board_token, c=company_name: {
                "source": "greenhouse",
                "source_id": job["id"],
                "board_token": t,
                "title": job["title"],
                "location": (job.get("location") or {}).get("name", ""),
                "url": job["absolute_url"],
                "company": c,
                "market": "International (remote)",
            },
        )

    for token, company_name in fetch_lever_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda t=token: fetch_lever_jobs.fetch_jobs(t),
            lambda posting, c=company_name: {
                "source": "lever",
                "source_id": posting["id"],
                "raw": posting,
                "title": posting["text"],
                "location": fetch_lever_jobs.normalize_location(posting),
                "url": posting["hostedUrl"],
                "company": c,
                "market": "International (remote)",
            },
        )

    for account, company_name in fetch_workable_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda a=account: fetch_workable_jobs.fetch_jobs(a),
            lambda job, c=company_name: {
                "source": "workable",
                "source_id": job["shortcode"],
                "raw": job,
                "title": job["title"],
                "location": fetch_workable_jobs.normalize_location(job),
                "url": job["url"],
                "company": c,
                "market": "International (remote)",
            },
        )

    for company_id, company_name in fetch_smartrecruiters_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda i=company_id: fetch_smartrecruiters_jobs.fetch_jobs(i),
            lambda posting, i=company_id, c=company_name: {
                "source": "smartrecruiters",
                "source_id": posting["id"],
                "company_id": i,
                "title": posting["name"],
                "location": posting.get("location", {}).get("fullLocation", ""),
                "url": fetch_smartrecruiters_jobs.POSTING_URL_TEMPLATE.format(
                    company_id=i, posting_id=posting["id"]
                ),
                "company": c,
                "market": "International (remote)",
            },
        )

    for token, company_name in fetch_ashby_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda t=token: fetch_ashby_jobs.fetch_jobs(t),
            lambda job, c=company_name: {
                "source": "ashby",
                "source_id": job["id"],
                "raw": job,
                "title": job["title"],
                "location": job.get("location", ""),
                "url": job.get("jobUrl") or job.get("applyUrl"),
                "company": c,
                "market": "International (remote)",
            },
        )

    for subdomain, company_name in fetch_gupy_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda s=subdomain: fetch_gupy_jobs.fetch_jobs(s),
            lambda job, s=subdomain, c=company_name: {
                "source": "gupy",
                "source_id": job["id"],
                "subdomain": s,
                "title": job["title"],
                "location": fetch_gupy_jobs.normalize_location(job),
                "url": fetch_gupy_jobs.job_url(s, job["id"]),
                "company": c,
                "market": "Brazilian market (local)",
            },
        )

    for company_key, company_name in fetch_workday_jobs.COMPANIES.items():
        _collect_provider(
            all_jobs, company_name,
            lambda k=company_key: fetch_workday_jobs.fetch_jobs(k),
            lambda job, k=company_key, c=company_name: _map_workday(job, k, c),
        )

    return all_jobs


def _map_workday(job, company_key, company_name):
    """Workday's full catalog (blank searchText) occasionally returns a
    record with no externalPath -- the field every downstream URL and id
    is built from. Such a posting cannot be linked to or re-fetched, so
    it is dropped deliberately rather than allowed to raise."""
    external_path = job.get("externalPath")
    if not external_path:
        return None
    return {
        "source": "workday",
        "source_id": external_path,
        "company_key": company_key,
        "external_path": external_path,
        "title": job.get("title", ""),
        "location": job.get("locationsText", ""),
        "url": fetch_workday_jobs.job_url(company_key, external_path),
        "company": company_name,
        "market": "International (remote)",
    }


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def score_batch(client, batch):
    jobs_text = "\n".join(
        f"- id={i}, title=\"{job['title']}\", location=\"{job['location']}\", company=\"{job['company']}\", "
        f"description=\"{job.get('description_excerpt', '')}\""
        for i, job in enumerate(batch)
    )
    prompt = SCORING_INSTRUCTIONS.format(profile=CANDIDATE_PROFILE, jobs=jobs_text)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def _fetch_job_detail(job):
    """Fetch (or, for providers whose listing payload already includes
    full detail, just return) the raw detail payload for one posting.
    Raises on network failure -- caller decides how to handle that."""
    source = job["source"]
    if source == "greenhouse":
        return fetch_greenhouse_jobs.fetch_job_detail(job["board_token"], job["source_id"])
    if source in ("lever", "workable", "ashby"):
        return job["raw"]
    if source == "smartrecruiters":
        return fetch_smartrecruiters_jobs.fetch_job_detail(job["company_id"], job["source_id"])
    if source == "gupy":
        return fetch_gupy_jobs.fetch_job_detail(job["subdomain"], job["source_id"])
    if source == "workday":
        return fetch_workday_jobs.fetch_job_detail(job["company_key"], job["external_path"])
    return {}


def _description_html(detail, source):
    if source == "greenhouse":
        return detail.get("content", "")
    if source == "lever":
        return detail.get("description", "")
    if source == "workable":
        return detail.get("description", "")
    if source == "smartrecruiters":
        sections = detail.get("jobAd", {}).get("sections", {})
        return " ".join(s.get("text", "") for s in sections.values())
    if source == "ashby":
        return detail.get("descriptionHtml", "")
    if source == "gupy":
        return (
            detail.get("description", "")
            + detail.get("prerequisites", "")
            + detail.get("responsibilities", "")
        )
    if source == "workday":
        return detail.get("jobDescription", "")
    return ""


def _extract_salary(detail, source):
    if source == "greenhouse":
        return extract_salary(detail)
    if source == "lever":
        return extract_salary_lever(detail)
    if source == "workable":
        return extract_salary_workable(detail)
    if source == "smartrecruiters":
        return extract_salary_smartrecruiters(detail)
    if source == "ashby":
        return extract_salary_ashby(detail)
    if source == "gupy":
        return "Not disclosed"  # Gupy never structurally discloses salary
    if source == "workday":
        return extract_salary_workday(detail)
    return "Not disclosed"


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()

    all_jobs = collect_all_jobs()

    # Geography is the only pre-scoring filter (see _is_location_eligible
    # docstring) -- title is never used to decide whether a posting is
    # worth fetching or how it's judged. Every location-eligible posting
    # gets its full description fetched here, *before* scoring, so
    # score_batch() can judge real responsibilities/requirements rather
    # than guessing from a title string.
    eligible_jobs = [job for job in all_jobs if _is_location_eligible(job)]
    print(
        f"{len(all_jobs)} fetched, {len(eligible_jobs)} location-eligible "
        f"(Brazil/LATAM-explicit or ambiguous/bare-remote) -- fetching full "
        f"descriptions for these before scoring.",
        file=sys.stderr,
    )

    detail_cache = {}  # url -> provider detail/raw posting payload
    for job in eligible_jobs:
        try:
            detail = _fetch_job_detail(job)
        except Exception as exc:
            print(f"Warning: failed to fetch detail for {job['title']} ({job['company']}): {exc}", file=sys.stderr)
            job["description_excerpt"] = ""
            continue
        detail_cache[job["url"]] = detail
        description_text = _strip_html_to_text(_description_html(detail, job["source"]))
        job["description_excerpt"] = description_text[:DESCRIPTION_EXCERPT_LENGTH]

    scored = []
    for batch in chunk(eligible_jobs, BATCH_SIZE):
        try:
            results = score_batch(client, batch)
        except Exception as exc:
            print(f"Warning: failed to score a batch of {len(batch)} jobs: {exc}", file=sys.stderr)
            continue
        for result in results:
            idx = result.get("id")
            if not isinstance(idx, int) or not (0 <= idx < len(batch)):
                continue
            job = batch[idx]
            scored.append(
                {
                    **job,
                    "score": result["score"],
                    "reason": result["reason"],
                    "category": result.get("category", "Adjacent"),
                    "level": result.get("level", "Primary"),
                    "probability": result.get("probability", "Medium"),
                    "trajectory": result.get("trajectory", ""),
                }
            )

    # The MIN_SCORE floor is applied inside process_run(), which gates
    # entry into tracking while still refreshing anything already tracked.
    # Salary/relocation enrichment below is only worth doing for jobs that
    # can actually reach the report, so screen to the floor here too --
    # process_run() re-applies it as the authoritative check.
    matches = [job for job in scored if job["score"] >= MIN_SCORE]
    matches.sort(key=lambda job: job["score"], reverse=True)

    # Detail was already fetched above (pre-score) for every eligible
    # job, including every match -- reuse it rather than fetching again.
    for job in matches:
        detail = detail_cache.get(job["url"], {})
        job["salary"] = _extract_salary(detail, job["source"])

    def description_html(url, source):
        return _description_html(detail_cache.get(url, {}), source)

    for job in matches:
        job["relocation"] = detect_relocation_support(description_html(job["url"], job["source"]))

    def cover_letter_fn(state_job):
        url = state_job["postings"][0]["url"]
        source = next((m["source"] for m in matches if m["url"] == url), "greenhouse")
        try:
            letter = generate_cover_letter_via_claude(
                client, state_job, description_html(url, source), CANDIDATE_PROFILE, MODEL
            )
            return save_cover_letter(state_job, letter)
        except Exception as exc:
            print(f"Warning: failed to draft cover letter for {state_job['title']}: {exc}", file=sys.stderr)
            return None

    def resume_bullets_fn(state_job):
        url = state_job["postings"][0]["url"]
        source = next((m["source"] for m in matches if m["url"] == url), "greenhouse")
        try:
            bullets = generate_resume_bullets_via_claude(
                client, state_job, description_html(url, source), CANDIDATE_PROFILE, MODEL
            )
            return save_resume_bullets(state_job, bullets)
        except Exception as exc:
            print(f"Warning: failed to draft resume bullets for {state_job['title']}: {exc}", file=sys.stderr)
            return None

    def salary_estimate_fn(state_job):
        if state_job.get("market") == "Brazilian market (local)":
            return estimate_br_salary(state_job["title"])
        try:
            return estimate_salary_via_claude(client, state_job, MODEL)
        except Exception as exc:
            print(f"Warning: failed to estimate salary for {state_job['title']}: {exc}", file=sys.stderr)
            return None

    new_matches, interested_matches, applied_matches, state = process_run(
        matches, cover_letter_fn, salary_estimate_fn, resume_bullets_fn
    )

    newly_expired = check_expired_links(state)

    print(f"{len(new_matches)} new matches this run, {len(applied_matches)} applied, "
          f"{len(interested_matches)} interested, {len(newly_expired)} newly expired "
          f"(out of {len(scored)} scored, {len(all_jobs)} fetched)\n")
    for job in new_matches:
        location = f" ({job['location']})" if job["location"] else ""
        print(f"[{job['score']}] {job['title']} — {job['company']}{location} [{job['category']}, {job['probability']}]")
        print(job["postings"][0]["url"])
        print(f"Salary: {job['salary']}" + (f" (est: {job['salary_estimate']})" if job.get("salary_estimate") else ""))
        if job.get("relocation"):
            print(f"Relocation support: {job['relocation']}")
        if job.get("col_note"):
            print(f"COL: {job['col_note']}")
        print(job["reason"])
        print(job["trajectory"])
        print()

    report_path = write_report(
        new_matches, interested_matches, applied_matches, len(scored), len(all_jobs), state
    )
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
