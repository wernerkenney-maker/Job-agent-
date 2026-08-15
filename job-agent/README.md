# job-agent

Tools for finding remote clinical operations / quality / regulatory
affairs / medical affairs / adjacent pharma-biotech leadership roles
(work-from-Brazil required).

## Fetching listings

Two provider modules, one per ATS, both with the same shape (`COMPANIES`
dict of token → display name, plus a `fetch_jobs()`):

- `fetch_greenhouse_jobs.py` — Greenhouse boards:
  - **Iovance Biotherapeutics** — clinical-stage biotech (cell therapy)
  - **Precision Medicine Group** — CRO, roles explicitly open to
    Remote/Brazil, Remote/LATAM
  - **Precision for Medicine** — CRO business unit of Precision Medicine
    Group, also has Brazil/LATAM-remote clinical roles
  - **Precision AQ** — health economics/market access unit of the same
    Precision Medicine Group family (no Brazil/LATAM roles currently,
    but tracked in case that changes)
  - **ClinChoice** — global CRO with Brazil-based listings
- `fetch_lever_jobs.py` — Lever boards:
  - **Alimentiv** — established CRO (GI/inflammation focus), broad
    international remote hiring (Europe, Africa, India, Canada, US) and
    historical evidence of a LATAM-scoped regulatory posting, though
    none are live as of this check — tracked so future Brazil/LATAM
    postings get caught automatically.

`companies.py` holds `COMPANY_FAMILIES`, mapping sibling boards from the
same corporate group across *either* provider (currently all three
Precision entities) so duplicate postings of the same role can be
deduped — see "Deduplication" below.

```
pip install -r requirements.txt
python3 fetch_greenhouse_jobs.py
python3 fetch_lever_jobs.py
```

**Note on Thermo Fisher:** its careers site (jobs.thermofisher.com) runs
on Phenom People, not Greenhouse or Lever, so no matching public-API
endpoint exists on either provider.

**Company search notes** (useful context before re-searching):

*Greenhouse* — confirmed *not* present (or present with zero Brazil/LATAM
postings) after an extensive search: major CROs `medable`, `curebase`,
`advarra`, `icon` (an empty "ICON Talent Community" board, not ICON plc),
`fortrea`, `veevasystems`, `certara`, `iqvia`, `parexel`, `syneoshealth`,
`medpace`, `ppd`, `worldwideclinicaltrials`, `biorasi`, and many more —
most large CROs run on Workday/other enterprise ATS. Standalone biotechs
that *are* on Greenhouse (Natera, Blueprint Medicines, Revolution
Medicines, Praxis, etc.) have zero Brazil/LATAM-remote postings even when
sizeable.

*Lever* — checked ARTBio, Capstan Medical, Orca Bio, ProTrials: real
companies, no Lever presence for some, zero Brazil/LATAM signal for the
rest (mostly US-onsite). Two names that surfaced repeatedly in search
were deliberately **excluded**, not just unmatched:
- **Jobgether** (`jobgether`) — not a CRO/biotech/pharma employer; a
  third-party AI-matching recruiting layer that reposts ~4,000 jobs
  across every industry and routes applications through its own
  screening rather than straight to the employer.
- **Welo Global** (`weloglobal`) — despite a "Life Sciences" business
  line, its actual Brazil-tagged postings are generic crowdsourced
  data-annotation/BPO gig work (e.g. "Ads Quality Rater"), not clinical
  roles.

Genuine Brazil/LATAM remote hiring in this space appears concentrated in
CROs with an explicit global-delivery staffing model (the Precision
family, ClinChoice) rather than single-asset biotechs or job-board
intermediaries.

## Resume-based matching

`match_jobs.py` fetches jobs from every company across both providers,
sends them to Claude in batches to score fit (1-100) against a candidate
background hardcoded in `CANDIDATE_PROFILE`, keeps jobs scoring 60+
(`MIN_SCORE`), then runs them through the shared pipeline (dedup, seen-job
tracking, salary, cover letters — see below) before writing the report.
Each batch uses its own local integer ids (0, 1, 2, ...) when talking to
Claude, since Lever ids are UUID strings rather than Greenhouse's
integers — keeps the scoring prompt/response format identical either way.

The scoring rubric is intentionally broader than an exact title match:
it considers clinical operations, quality, regulatory affairs, medical
affairs, and other pharma/biotech leadership functions, and prioritizes
compensation and long-term career trajectory over title wording — a
strong adjacent-function role at equal-or-better seniority/pay scores as
well as (or better than) a narrower title match at a lower level (e.g. a
"Consultant"/"Associate"-level contract role scores lower than a
permanent managerial/director-level role, even in a closer-sounding
function). The one hard requirement that isn't traded off: the role must
plausibly be performable remotely from Brazil — anything else is capped
at 40 regardless of functional fit. See `SCORING_INSTRUCTIONS` in
`match_jobs.py` for the exact prompt.

```
export ANTHROPIC_API_KEY=sk-ant-...
pip install -r requirements.txt
python3 match_jobs.py
```

Edit `CANDIDATE_PROFILE` at the top of `match_jobs.py` to update the
background used for scoring. `CLAUDE_MODEL` env var overrides the model
(defaults to `claude-sonnet-5`).

## Deduplication

`dedup.py` groups raw per-posting matches by (corporate family, normalized
title) and merges each group into one match with a `postings` list (each
entry: company + url + location). This is why, e.g., "Clinical Trial
Manager (LATAM)" posted separately on the Precision Medicine Group and
Precision for Medicine boards shows up once in the report, with a
"also posted by" link to the sibling.

## Seen-job tracking & status

`jobs_state.py` persists every match ever seen (score 60+, post-dedup) in
`jobs_state.json`, keyed by (corporate family, normalized title) so it
survives postings moving between sibling boards or getting reposted with
a new Greenhouse job ID. Each run only surfaces matches that are new
since the last run — a match that scored 60+ before and hasn't been
acted on doesn't clutter every future report.

Each tracked job has a `status`: `new` (default), `interested`,
`applied`, or `pass`. Set it with:

```
python3 set_status.py <posting-url> applied|interested|pass
```

(any of a job's apply links works, even after dedup). `report.html` shows
two sections: **New matches** (first time crossing 60+ this run) and
**Tracked** (anything marked `interested` or `applied`, so you don't lose
track of applications in progress). Jobs marked `pass` are hidden from
the report entirely but stay in `jobs_state.json` for the record.
Re-run `match_jobs.py` / `apply_manual_scores.py` after changing a status
to refresh the report.

## Salary

`salary.py` extracts a **disclosed** salary range using only structural
signals from the posting itself:
- Greenhouse (`extract_salary()`) — a pay-transparency metadata field
  (Precision Medicine Group/Precision for Medicine) or a pay-transparency
  widget embedded in the job description HTML (Iovance Biotherapeutics).
- Lever (`extract_salary_lever()`) — the native `salaryRange` field Lever
  exposes directly in the listing (no extra request needed, unlike
  Greenhouse which requires a per-job detail fetch), falling back to the
  poster's own `salaryDescription` text field if present.

It never guesses at a number from free-text mentions elsewhere in the
job description (e.g. budget/revenue figures).

When nothing is structurally disclosed (the norm for non-US postings),
`salary_estimate.py` provides a rough, clearly-labeled **market-rate
estimate** instead (e.g. `"~$60,000–$90,000 USD (estimated — ..., not
disclosed by employer)"`) — for the live path, generated by asking Claude
for a conservative range grounded in general industry knowledge of the
role's function/seniority/location; for the manual path, filled in by
Claude directly and recorded in `manual_extras.json`. This is always
presented as an estimate, styled distinctly (italic) from a real
disclosed figure, never asserted as fact.

## Cover letters & resume bullets

For any match scoring 80+, two things get drafted via Claude and saved
for review/editing — never auto-submitted anywhere:
- `cover_letter.py` — a short, tailored cover letter (using
  `CANDIDATE_PROFILE` and the job description), saved to
  `cover_letters/<slug>.md`.
- `resume_bullets.py` — 3-4 rewritten resume bullets pulling only from
  `CANDIDATE_PROFILE`'s real experience, reordered/reworded to foreground
  whatever's most relevant to that specific role (never inventing new
  accomplishments or numbers), saved to `resume_bullets/<slug>.md`.

The report links to both under the job card. Both backfill automatically
for any job that crosses 80+ later, even if it was first seen at a lower
score in a previous run — and independently of each other, so if one was
already drafted (e.g. in an earlier version of this tool) the other still
gets backfilled without regenerating the first.

Note: these links only render on jobs currently shown in the report (the
"New matches" or "Tracked" section). A job that already had drafts
generated but has since scrolled out of "new" (seen before, no status
set) still has both files in the repo — just re-check `jobs_state.json`
for its `cover_letter_path`/`resume_bullets_path`, or mark it
`interested`/`applied` with `set_status.py` to bring it back into the
Tracked section.

## HTML report

`report.py` renders `report.html` — a single self-contained,
mobile-friendly page (score badge, clickable title linking straight to
the posting, company, location, salary/estimate, one-line reason, sibling
links, cover letter + resume bullets links, status), styled for light and
dark mode, no
external dependencies.

`match_jobs.py` regenerates `report.html` automatically at the end of
every run, after routing matches through `pipeline.process_run()`
(dedup → seen-job/state update → cover letter & salary-estimate backfill).

When no `ANTHROPIC_API_KEY` is available and scoring is instead done
manually (e.g. by Claude directly in a chat session): record raw
per-posting matches in `manual_matches.json` (including a real,
API-verified `salary` value per posting — never invented), record any
cover letter text / salary estimate figures for this run in
`manual_extras.json`, then run:

```
python3 apply_manual_scores.py
```

This goes through the same `pipeline.process_run()` and `write_report()`
as `match_jobs.py`, so `report.html` is produced identically regardless
of whether the matches came from a live run or a manual scoring pass.
