#!/usr/bin/env python3
"""Fetch jobs from the configured Greenhouse boards, score each one for fit
against a candidate's background using Claude, dedupe sibling postings,
track which matches are new since the last run, draft cover letters for
80+ scores, estimate salary where undisclosed, and refresh report.html.

Requires an Anthropic API key in the ANTHROPIC_API_KEY environment variable.
"""

import json
import os
import sys

import anthropic

from cover_letter import generate_cover_letter_via_claude, save_cover_letter
from fetch_greenhouse_jobs import COMPANIES, fetch_job_detail, fetch_jobs
from pipeline import process_run
from report import write_report
from salary import extract_salary
from salary_estimate import estimate_salary_via_claude

CANDIDATE_PROFILE = """
Portfolio Manager at Labcorp Clinical Laboratory Services (Labcorp CLS),
overseeing 100+ global clinical studies and $200M+ in annual revenue.
Previously Global Clinical Study Manager, managing $20M+ trial budgets
across Oncology, Autoimmune, and Malaria trials. Before that, Regional
Study Coordinator, EMEA. Certificate in Project Management from Rutgers.
Fluent in English and Portuguese; working proficiency in German.
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

Hard requirement: the role must plausibly be performable remotely from
Brazil (location explicitly includes Brazil, or a LATAM-inclusive remote
scope). If it does not, score it no higher than 40 regardless of how
strong the functional fit is.

For each job below, score fit from 1 (no fit) to 100 (excellent fit).

Jobs:
{jobs}

Respond with ONLY a JSON array, no other text, in this exact form:
[{{"id": <job id, integer>, "score": <integer 1-100>, "reason": "<one-line reason, under 20 words>"}}, ...]
Include exactly one entry per job listed above, in any order.
"""


def collect_all_jobs():
    all_jobs = []
    for board_token, company_name in COMPANIES.items():
        try:
            jobs = fetch_jobs(board_token)
        except Exception as exc:
            print(f"Failed to fetch {company_name}: {exc}", file=sys.stderr)
            continue
        for job in jobs:
            all_jobs.append(
                {
                    "id": job["id"],
                    "title": job["title"],
                    "location": (job.get("location") or {}).get("name", ""),
                    "url": job["absolute_url"],
                    "company": company_name,
                }
            )
    return all_jobs


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def score_batch(client, batch):
    jobs_text = "\n".join(
        f"- id={job['id']}, title=\"{job['title']}\", location=\"{job['location']}\", company=\"{job['company']}\""
        for job in batch
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
    jobs_by_id = {job["id"]: job for job in all_jobs}

    scored = []
    for batch in chunk(all_jobs, BATCH_SIZE):
        try:
            results = score_batch(client, batch)
        except Exception as exc:
            print(f"Warning: failed to score a batch of {len(batch)} jobs: {exc}", file=sys.stderr)
            continue
        for result in results:
            job = jobs_by_id.get(result.get("id"))
            if job is None:
                continue
            scored.append({**job, "score": result["score"], "reason": result["reason"]})

    matches = [job for job in scored if job["score"] >= MIN_SCORE]
    matches.sort(key=lambda job: job["score"], reverse=True)

    board_token_by_company = {v: k for k, v in COMPANIES.items()}
    detail_cache = {}
    for job in matches:
        board_token = board_token_by_company[job["company"]]
        try:
            detail = fetch_job_detail(board_token, job["id"])
            detail_cache[job["url"]] = detail
            job["salary"] = extract_salary(detail)
        except Exception as exc:
            print(f"Warning: failed to fetch salary for job {job['id']}: {exc}", file=sys.stderr)
            job["salary"] = "Not disclosed"

    def cover_letter_fn(state_job):
        detail = detail_cache.get(state_job["postings"][0]["url"], {})
        try:
            letter = generate_cover_letter_via_claude(
                client, state_job, detail.get("content", ""), CANDIDATE_PROFILE, MODEL
            )
            return save_cover_letter(state_job, letter)
        except Exception as exc:
            print(f"Warning: failed to draft cover letter for {state_job['title']}: {exc}", file=sys.stderr)
            return None

    def salary_estimate_fn(state_job):
        try:
            return estimate_salary_via_claude(client, state_job, MODEL)
        except Exception as exc:
            print(f"Warning: failed to estimate salary for {state_job['title']}: {exc}", file=sys.stderr)
            return None

    new_matches, tracked_matches, state = process_run(matches, cover_letter_fn, salary_estimate_fn)

    print(f"{len(new_matches)} new matches this run, {len(tracked_matches)} tracked "
          f"(out of {len(scored)} scored, {len(all_jobs)} fetched)\n")
    for job in new_matches:
        location = f" ({job['location']})" if job["location"] else ""
        print(f"[{job['score']}] {job['title']} — {job['company']}{location}")
        print(job["postings"][0]["url"])
        print(f"Salary: {job['salary']}" + (f" (est: {job['salary_estimate']})" if job.get("salary_estimate") else ""))
        print(job["reason"])
        print()

    report_path = write_report(new_matches, tracked_matches, len(scored), len(all_jobs))
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
