# job-agent

Tools for finding remote clinical trials / clinical operations roles
(work-from-Brazil friendly).

## Current state

`fetch_greenhouse_jobs.py` fetches open listings from several companies'
public Greenhouse job board APIs and prints each job's title and link,
grouped by company.

Usage:

```
pip install -r requirements.txt
python3 fetch_greenhouse_jobs.py
```

Companies checked (`COMPANIES` dict in the script — add/remove
Greenhouse board tokens there):

- **Iovance Biotherapeutics** — clinical-stage biotech (cell therapy)
- **Precision Medicine Group** — CRO, has roles explicitly open to
  Remote/Brazil, Remote/LATAM
- **Precision for Medicine** — CRO business unit of Precision Medicine
  Group, also has Brazil/LATAM-remote clinical roles (Clinical Trial
  Manager (LATAM), Investigator Grants Associate (Brazil), etc.)
- **ClinChoice** — global CRO with a Brazil-based listing

**Note on Thermo Fisher:** Thermo Fisher's careers site
(jobs.thermofisher.com) runs on Phenom People, not Greenhouse, so there is
no `boards-api.greenhouse.io/v1/boards/thermofisher/jobs` endpoint. Fetching
Thermo Fisher's actual listings will need a separate script against its
real source (Phenom People) — planned as a next step.

Other Greenhouse tokens tried and confirmed *not* to exist for major
CROs/biotechs (in case useful later): `medable`, `curebase`, `advarra`,
`icon` (returns an empty "ICON Talent Community" board, not ICON plc),
`fortrea`, `veevasystems`, `certara`.

## Resume-based matching

`match_jobs.py` fetches jobs from all companies in `COMPANIES` (reusing
`fetch_greenhouse_jobs.py`), sends them to Claude in batches to score fit
(1-100) against a candidate background hardcoded in `CANDIDATE_PROFILE`,
then prints only jobs scoring 60+ (`MIN_SCORE`), sorted highest first,
each with a one-line reason and a salary line.

The scoring rubric is intentionally broader than an exact title match:
it considers clinical operations, quality, regulatory affairs, medical
affairs, and other pharma/biotech leadership functions, and prioritizes
compensation and long-term career trajectory over title wording — a
strong adjacent-function role at equal-or-better seniority/pay scores as
well as (or better than) a narrower title match at a lower level. The
one hard requirement that isn't traded off: the role must plausibly be
performable remotely from Brazil (explicit Brazil location, or a
LATAM-inclusive remote scope) — anything else is capped at 40 regardless
of functional fit. See `SCORING_INSTRUCTIONS` in `match_jobs.py` for the
exact prompt.

Requires an Anthropic API key:

```
export ANTHROPIC_API_KEY=sk-ant-...
pip install -r requirements.txt
python3 match_jobs.py
```

Edit `CANDIDATE_PROFILE` at the top of `match_jobs.py` to update the
background used for scoring. `CLAUDE_MODEL` env var overrides the model
(defaults to `claude-sonnet-5`).

## Salary

`salary.py` extracts a disclosed salary range for each matched job, using
only structural signals from the Greenhouse posting itself — a
pay-transparency metadata field (companies like Precision Medicine
Group/Precision for Medicine) or a pay-transparency widget embedded in
the job description HTML (companies like Iovance Biotherapeutics). It
never guesses at a number from free-text mentions elsewhere in the
description (e.g. budget/revenue figures) — if neither structural signal
is present, it reports `"Not disclosed"`, which is the norm for non-US
postings. `match_jobs.py` fetches this per matched job (not for every
job fetched, to keep API calls bounded) via
`fetch_greenhouse_jobs.fetch_job_detail()`.

## HTML report

`report.py` renders the scored matches into `report.html` — a single
self-contained, mobile-friendly page (score badge, clickable title
linking straight to the posting, company, location, salary, one-line
reason), styled for both light and dark mode. It has no external
dependencies, so it can be opened directly in a browser or hosted
anywhere (e.g. GitHub Pages).

`match_jobs.py` regenerates `report.html` automatically at the end of
every run (via `write_report()` in `report.py`).

When no `ANTHROPIC_API_KEY` is available and scoring is instead done
manually (e.g. by Claude directly in a chat session), record the results
in `manual_matches.json` (including a real, API-verified `salary` value
per job — never an invented one) and run:

```
python3 apply_manual_scores.py
```

This calls the same `write_report()` function, so `report.html` is
produced identically regardless of whether the matches came from a live
`match_jobs.py` run or a manual scoring pass.
