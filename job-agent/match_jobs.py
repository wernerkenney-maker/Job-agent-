#!/usr/bin/env python3
"""Fetch jobs from the configured Greenhouse, Lever, Workable,
SmartRecruiters, Ashby, and Gupy (Brazilian-market) boards, score each one
for fit against a candidate's background using Claude, dedupe sibling
postings, track which matches are new since the last run, draft cover
letters + tailored resume bullets for 80+ scores, estimate salary where
undisclosed, and refresh report.html.

Requires an Anthropic API key in the ANTHROPIC_API_KEY environment variable.
"""

import json
import os
import sys

import anthropic

import fetch_ashby_jobs
import fetch_greenhouse_jobs
import fetch_gupy_jobs
import fetch_lever_jobs
import fetch_smartrecruiters_jobs
import fetch_workable_jobs
from br_salary_estimate import estimate_br_salary
from cover_letter import generate_cover_letter_via_claude, save_cover_letter
from pipeline import process_run
from relocation import detect_relocation_support
from report import write_report
from resume_bullets import generate_resume_bullets_via_claude, save_resume_bullets
from salary import (
    extract_salary,
    extract_salary_ashby,
    extract_salary_lever,
    extract_salary_smartrecruiters,
    extract_salary_workable,
)
from salary_estimate import estimate_salary_via_claude

CANDIDATE_PROFILE = """
Portfolio Manager at Labcorp Clinical Laboratory Services (Labcorp CLS),
overseeing 100+ global clinical studies and $200M+ in annual revenue.
Previously Global Clinical Study Manager, managing $20M+ trial budgets
across Oncology, Autoimmune, and Malaria trials. Before that, Regional
Study Coordinator, EMEA. Certificate in Project Management from Rutgers.
Fluent in English and Portuguese; working proficiency in German. Based
in Fortaleza, Brazil.
""".strip()

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
MIN_SCORE = 60
BATCH_SIZE = 40

SCORING_INSTRUCTIONS = """
You are screening job listings for fit against a candidate's background.

Candidate background:
{profile}

The candidate is not limited to their exact current title. Score roles
across clinical operations, quality, regulatory affairs, medical affairs,
or other pharma/biotech leadership functions where their experience
(large-scale trial/portfolio management, multi-million dollar budgets,
cross-functional and cross-regional leadership) is a strong transferable
fit. Prioritize compensation and long-term career trajectory over an
exact title match: a role in an adjacent function at equal-or-better
seniority, pay, and growth potential should score as well as or better
than a narrower title match at a lower level (e.g. a "Consultant" or
"Associate"-level contract role should score lower than a permanent
managerial/director-level role, even in a closer-sounding function).

Hard requirement: the role must be workable from Brazil -- either
explicitly remote/LATAM-inclusive, OR physically located on-site/hybrid
within Brazil (any city; the candidate is based in Fortaleza but is open
to relocating for the right on-site/hybrid role). If neither is true,
score it no higher than 40 regardless of how strong the functional fit
is.

For each job below, also determine:
- category: "In-field" if it's direct clinical operations / clinical
  trial management work, or "Adjacent" if it's a transferable-skills fit
  outside that (regulatory, quality, program/portfolio leadership outside
  pharma, general operations, etc.).
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
[{{"id": <batch-local integer id>, "score": <integer 1-100>, "reason": "<one-line reason, under 20 words>", "category": "In-field|Adjacent", "probability": "High|Medium|Long-shot", "trajectory": "<one-line note, under 20 words>"}}, ...]
Include exactly one entry per job listed above, in any order.
"""


def collect_all_jobs():
    all_jobs = []

    for board_token, company_name in fetch_greenhouse_jobs.COMPANIES.items():
        try:
            jobs = fetch_greenhouse_jobs.fetch_jobs(board_token)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for job in jobs:
            all_jobs.append(
                {
                    "source": "greenhouse",
                    "source_id": job["id"],
                    "board_token": board_token,
                    "title": job["title"],
                    "location": (job.get("location") or {}).get("name", ""),
                    "url": job["absolute_url"],
                    "company": company_name,
                    "market": "International (remote)",
                }
            )

    for token, company_name in fetch_lever_jobs.COMPANIES.items():
        try:
            postings = fetch_lever_jobs.fetch_jobs(token)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for posting in postings:
            all_jobs.append(
                {
                    "source": "lever",
                    "source_id": posting["id"],
                    "raw": posting,
                    "title": posting["text"],
                    "location": fetch_lever_jobs.normalize_location(posting),
                    "url": posting["hostedUrl"],
                    "company": company_name,
                    "market": "International (remote)",
                }
            )

    for account, company_name in fetch_workable_jobs.COMPANIES.items():
        try:
            jobs = fetch_workable_jobs.fetch_jobs(account)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for job in jobs:
            all_jobs.append(
                {
                    "source": "workable",
                    "source_id": job["shortcode"],
                    "raw": job,
                    "title": job["title"],
                    "location": fetch_workable_jobs.normalize_location(job),
                    "url": job["url"],
                    "company": company_name,
                    "market": "International (remote)",
                }
            )

    for company_id, company_name in fetch_smartrecruiters_jobs.COMPANIES.items():
        try:
            postings = fetch_smartrecruiters_jobs.fetch_jobs(company_id)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for posting in postings:
            all_jobs.append(
                {
                    "source": "smartrecruiters",
                    "source_id": posting["id"],
                    "company_id": company_id,
                    "title": posting["name"],
                    "location": posting.get("location", {}).get("fullLocation", ""),
                    "url": fetch_smartrecruiters_jobs.POSTING_URL_TEMPLATE.format(
                        company_id=company_id, posting_id=posting["id"]
                    ),
                    "company": company_name,
                    "market": "International (remote)",
                }
            )

    for token, company_name in fetch_ashby_jobs.COMPANIES.items():
        try:
            jobs = fetch_ashby_jobs.fetch_jobs(token)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for job in jobs:
            all_jobs.append(
                {
                    "source": "ashby",
                    "source_id": job["id"],
                    "raw": job,
                    "title": job["title"],
                    "location": job.get("location", ""),
                    "url": job.get("jobUrl") or job.get("applyUrl"),
                    "company": company_name,
                    "market": "International (remote)",
                }
            )

    for subdomain, company_name in fetch_gupy_jobs.COMPANIES.items():
        try:
            jobs = fetch_gupy_jobs.fetch_jobs(subdomain)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for job in jobs:
            all_jobs.append(
                {
                    "source": "gupy",
                    "source_id": job["id"],
                    "subdomain": subdomain,
                    "title": job["title"],
                    "location": fetch_gupy_jobs.normalize_location(job),
                    "url": fetch_gupy_jobs.job_url(subdomain, job["id"]),
                    "company": company_name,
                    "market": "Brazilian market (local)",
                }
            )

    return all_jobs


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def score_batch(client, batch):
    jobs_text = "\n".join(
        f"- id={i}, title=\"{job['title']}\", location=\"{job['location']}\", company=\"{job['company']}\""
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


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()

    all_jobs = collect_all_jobs()

    scored = []
    for batch in chunk(all_jobs, BATCH_SIZE):
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
                    "probability": result.get("probability", "Medium"),
                    "trajectory": result.get("trajectory", ""),
                }
            )

    matches = [job for job in scored if job["score"] >= MIN_SCORE]
    matches.sort(key=lambda job: job["score"], reverse=True)

    detail_cache = {}  # url -> provider detail/raw posting payload
    for job in matches:
        try:
            if job["source"] == "greenhouse":
                detail = fetch_greenhouse_jobs.fetch_job_detail(job["board_token"], job["source_id"])
                detail_cache[job["url"]] = detail
                job["salary"] = extract_salary(detail)
            elif job["source"] == "lever":
                detail_cache[job["url"]] = job["raw"]
                job["salary"] = extract_salary_lever(job["raw"])
            elif job["source"] == "workable":
                detail_cache[job["url"]] = job["raw"]
                job["salary"] = extract_salary_workable(job["raw"])
            elif job["source"] == "smartrecruiters":
                detail = fetch_smartrecruiters_jobs.fetch_job_detail(job["company_id"], job["source_id"])
                detail_cache[job["url"]] = detail
                job["salary"] = extract_salary_smartrecruiters(detail)
            elif job["source"] == "ashby":
                detail_cache[job["url"]] = job["raw"]
                job["salary"] = extract_salary_ashby(job["raw"])
            elif job["source"] == "gupy":
                detail = fetch_gupy_jobs.fetch_job_detail(job["subdomain"], job["source_id"])
                detail_cache[job["url"]] = detail
                job["salary"] = "Not disclosed"  # Gupy never structurally discloses salary
        except Exception as exc:
            print(f"Warning: failed to fetch salary for {job['title']}: {exc}", file=sys.stderr)
            job["salary"] = "Not disclosed"

    def description_html(url, source):
        detail = detail_cache.get(url, {})
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
        return ""

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

    new_matches, tracked_matches, state = process_run(
        matches, cover_letter_fn, salary_estimate_fn, resume_bullets_fn
    )

    print(f"{len(new_matches)} new matches this run, {len(tracked_matches)} tracked "
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

    report_path = write_report(new_matches, tracked_matches, len(scored), len(all_jobs))
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
