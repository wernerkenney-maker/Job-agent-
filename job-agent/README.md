# job-agent

Tools for finding clinical operations / quality / regulatory affairs /
medical affairs / adjacent pharma-biotech leadership roles workable from
Brazil — remote, or on-site/hybrid anywhere in the country. Candidate is
based in Fortaleza.

## Fetching listings

Five provider modules, one per ATS, all with the same shape (`COMPANIES`
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
  - **Care Access** — decentralized clinical trial site network, 2
    Brazil-based roles (CTMS Operations Analyst, Specialist QA)
- `fetch_lever_jobs.py` — Lever boards:
  - **Alimentiv** — established CRO (GI/inflammation focus), broad
    international remote hiring (Europe, Africa, India, Canada, US) and
    historical evidence of a LATAM-scoped regulatory posting, though
    none are live as of this check — tracked so future Brazil/LATAM
    postings get caught automatically.
- `fetch_workable_jobs.py` — Workable boards:
  - **EDETEK** — eClinical/clinical-data CRO, multiple Brazil/LATAM
    postings (Clinical Data Manager, Senior Clinical Project Manager,
    Senior Clinical QA Specialist, etc.). Workable's endpoint 429s
    without a browser-like `User-Agent` header (and sometimes even with
    one) — `fetch_jobs()` retries with backoff.
- `fetch_smartrecruiters_jobs.py` — SmartRecruiters boards:
  - **PSI CRO** — established (founded 1995, 3,000+ employees), privately
    held global CRO, 12 Brazil-based postings across a range of seniority
    levels. The list endpoint doesn't include salary/full description —
    `fetch_job_detail()` fetches that per matched job, same pattern as
    Greenhouse.
- `fetch_ashby_jobs.py` — Ashby boards: `COMPANIES` is currently empty.
  Checked ~20 candidates (Iambic Therapeutics, myTomorrows, Paradigm,
  Unlearn, Triomics, and more) — real companies, no Brazil/LATAM-eligible
  postings as of this check. Ready to fetch (including compensation via
  `includeCompensation=true`) as soon as a genuine match turns up.

`companies.py` holds `COMPANY_FAMILIES`, mapping sibling boards from the
same corporate group across *any* provider (currently all three
Precision entities, all on Greenhouse) so duplicate postings of the same
role can be deduped — see "Deduplication" below.

```
pip install -r requirements.txt
python3 fetch_greenhouse_jobs.py
python3 fetch_lever_jobs.py
python3 fetch_workable_jobs.py
python3 fetch_smartrecruiters_jobs.py
python3 fetch_ashby_jobs.py
```

**Note on Thermo Fisher:** its careers site (jobs.thermofisher.com) runs
on Phenom People, not any of the five providers above, so no matching
public-API endpoint exists.

**Company search notes** (useful context before re-searching):

*Greenhouse* — confirmed *not* present (or present with zero Brazil/LATAM
postings) after an extensive search: major CROs `medable`, `curebase`,
`advarra`, `icon` (an empty "ICON Talent Community" board, not ICON plc),
`fortrea`, `veevasystems`, `certara`, `iqvia`, `parexel`, `syneoshealth`,
`medpace`, `ppd`, `worldwideclinicaltrials`, `biorasi`, and many more —
most large CROs run on Workday/other enterprise ATS. Standalone biotechs
that *are* on Greenhouse (Natera, Blueprint Medicines, Revolution
Medicines, Praxis, etc.) have zero Brazil/LATAM-remote postings even when
sizeable. **Care Access** was found later, while searching SmartRecruiters
— worth remembering that a company can surface from a search aimed at a
different provider.

*Lever* — checked ARTBio, Capstan Medical, Orca Bio, ProTrials: real
companies, no Lever presence for some, zero Brazil/LATAM signal for the
rest (mostly US-onsite).

*Workable* — `ethica-cro-inc` is real but has zero open postings.

*SmartRecruiters* — most guessed company identifiers for major CROs
(`ICON`, `IQVIA`, `Parexel`, `Syneos`, `Medpace`, `WCGClinical`,
`Advarra`, `Fortrea`, `PPD`, `Covance`, etc.) return `totalFound: 0` —
either not registered there or a stale/inactive presence. **PSI CRO**
was the one real hit. Also checked `OnPointClinicalStaffingServices` and
`IntegratedResourcesINC` (real staffing agencies, zero Brazil postings —
moot either way) and `M3usa` (healthcare market research, 13 Brazil
postings but all market-research/qualitative-research/translation gig
work, not clinical/quality/regulatory/medical-affairs — excluded as
out-of-scope function, not a fake-employer exclusion like the two below).

*Ashby* — checked ~20 real companies with zero Brazil/LATAM signal (see
`fetch_ashby_jobs.py`).

Two names that surfaced repeatedly across Lever and Ashby searches were
deliberately **excluded**, not just unmatched — neither is a real
CRO/biotech/pharma employer:
- **Jobgether** (Lever, `jobgether`) — a third-party AI-matching
  recruiting layer that reposts ~4,000 jobs across every industry and
  routes applications through its own screening rather than straight to
  the employer.
- **Welo Global** (Lever, `weloglobal`) / **The Global Talent Co.**
  (Ashby, `the-global-talent-co`) — staffing/BPO vendors; their
  Brazil-tagged postings are generic crowdsourced gig work ("Ads Quality
  Rater") or unrelated-industry contract roles (music-industry valuation,
  customer care), not clinical/pharma work.

Genuine Brazil/LATAM remote hiring in this space appears concentrated in
CROs with an explicit global-delivery staffing model (the Precision
family, ClinChoice, EDETEK, PSI CRO, Care Access) rather than
single-asset biotechs or job-board intermediaries.

## Resume-based matching

`match_jobs.py` fetches jobs from every company across all five
providers, sends them to Claude in batches to score fit (1-100) against a
candidate background hardcoded in `CANDIDATE_PROFILE`, keeps jobs scoring
60+ (`MIN_SCORE`), then runs them through the shared pipeline (dedup,
seen-job tracking, salary, cover letters — see below) before writing the
report. Each batch uses its own local integer ids (0, 1, 2, ...) when
talking to Claude instead of raw provider ids, since those differ in type
across providers (Greenhouse/SmartRecruiters use integers, Lever/Ashby
use UUID strings, Workable uses hex shortcodes) — keeps the scoring
prompt/response format identical regardless of source.

The scoring rubric is intentionally broader than an exact title match:
it considers clinical operations, quality, regulatory affairs, medical
affairs, and other pharma/biotech leadership functions, and prioritizes
compensation and long-term career trajectory over title wording — a
strong adjacent-function role at equal-or-better seniority/pay scores as
well as (or better than) a narrower title match at a lower level (e.g. a
"Consultant"/"Associate"-level contract role scores lower than a
permanent managerial/director-level role, even in a closer-sounding
function). The one hard requirement that isn't traded off: the role must
be workable from Brazil — either explicitly remote/LATAM-inclusive, or
physically on-site/hybrid anywhere in Brazil (the candidate is based in
Fortaleza but open to relocating for the right on-site/hybrid role) —
anything else is capped at 40 regardless of functional fit. See
`SCORING_INSTRUCTIONS` in `match_jobs.py` for the exact prompt.

## Category, probability, and trajectory

Alongside the score/reason, each match also gets three more fields (from
the same Claude scoring call, or filled in manually in
`manual_matches.json` on the manual path):
- **category** — `"In-field"` (direct clinical operations/trial
  management work) or `"Adjacent"` (transferable-skills fit elsewhere —
  regulatory, quality, program/portfolio leadership outside pharma,
  general operations, etc.).
- **probability** — `"High"`, `"Medium"`, or `"Long-shot"`, a realistic
  (not encouraging-by-default) read on how closely the candidate's actual
  experience maps to what the role likely requires — seniority, domain
  depth, therapeutic-area fit, language/region fit, etc. A role that
  *sounds* senior but needs deep therapeutic-area-specific experience the
  candidate doesn't have (e.g. a Gastroenterology-specific leadership
  role, when the candidate's therapeutic background is Oncology/
  Autoimmune/Malaria) should score as `"Long-shot"` even if the title fit
  looks strong.
- **trajectory** — one line on whether the role is a lateral move, a step
  up, or a bigger leap versus the candidate's current role, plus a
  plain-spoken read on whether it's worth pursuing even as a stretch.

These render as colored tags (category/probability) and a bordered
callout (trajectory) on each report card.

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
  Requires a per-job detail fetch.
- Lever (`extract_salary_lever()`) — the native `salaryRange` field,
  available directly in the listing (no extra request), falling back to
  the poster's own `salaryDescription` text field if present.
- Workable (`extract_salary_workable()`) — the native `salary_data`
  field, available directly in the listing.
- SmartRecruiters (`extract_salary_smartrecruiters()`) — a distinct
  "Compensation"/"Salary"/"Pay" section in the job ad, if the poster
  included one (not free text elsewhere in the ad). Requires a per-job
  detail fetch (the list endpoint doesn't include the full job ad).
- Ashby (`extract_salary_ashby()`) — the native
  `compensation.compensationTierSummary` field, available directly in the
  listing when the request includes `includeCompensation=true` and the
  employer opted into disclosure.

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

## Relocation support flag

`relocation.py` scans the job description's own text for explicit
mentions of relocation assistance, a home-office/equipment stipend, or a
sign-on bonus (regex against phrases like "relocation package", "sign-on
bonus", "home office stipend") — never inferred from company size, role
seniority, or anything else. If none of those phrases appear, the field
stays blank rather than guessing. Computed once per matched job at
scoring time (live path, from the fetched description) or recorded
manually per posting in `manual_matches.json` (manual path, after
actually reading the description) — carried through dedup and state like
every other field.

## Pace tracker

`pace_tracker.py` logs every job marked `applied` (once per job, even if
re-marked) to `applications_log.json`, timestamped. `set_status.py` calls
`log_application()` automatically whenever you run
`set_status.py <url> applied`. `report.html`'s header shows a running
"N applied this week · M all-time" count, computed fresh from the log on
every report generation — meant as a simple, durable way to see pace
toward an active search over the coming year, not a specific numeric
goal (none was set).

## City & cost-of-living comparison

`cost_of_living.py` extracts the specific city from a posting's location
(when one is named — a bare "Remote, Brazil" has none, and the field
stays blank) and, when a salary figure is available (disclosed or
estimated), adds a plain-language, **reais-denominated** comparison
against Fortaleza, e.g. *"~R$325.000–R$475.000 in São Paulo is roughly
equivalent to ~R$224.000–R$328.000 of purchasing power in Fortaleza
(São Paulo's cost of living runs roughly 45% higher than Fortaleza; both
figures rough estimates, using an approximate R$5.00/USD exchange
rate)."* Two stacked approximations go into this, both called out in the
note text itself:
- `FORTALEZA_COL_INDEX` — a rough, directional index (São Paulo/Rio
  meaningfully higher, southern/southeastern hub cities moderately
  higher, other northeastern cities close to Fortaleza) based on general
  knowledge, not a live cost-of-living dataset.
- `USD_TO_BRL_RATE` — since salary/estimate figures are USD, converting
  to reais needs an FX rate too; also illustrative, not a live quote
  (currently 5.00, revisit if it drifts noticeably).

Computed deterministically inside `pipeline.process_run()` on every run
(no API call), so it applies identically to both the live and manual
scoring paths and stays fresh if a job's salary/estimate changes.

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

The report links to both under the job card, pointed at the file's
GitHub blob URL (`report._github_blob_base_url()`, derived from `git
remote get-url origin` + the current branch) rather than a bare relative
path — a relative link only resolves when report.html is opened from
inside a checkout with those sibling files present, not when previewed
standalone (e.g. a sent-file viewer, which is how it's normally shared).
Falls back to a relative path if this isn't a pushed git checkout. Both
files backfill automatically for any job that crosses 80+ later, even if
it was first seen at a lower score in a previous run — and independently
of each other, so if one was already drafted (e.g. in an earlier version
of this tool) the other still gets backfilled without regenerating the
first.

Note: these links only render on jobs currently shown in the report (the
"New matches" or "Tracked" section). A job that already had drafts
generated but has since scrolled out of "new" (seen before, no status
set) still has both files in the repo — just re-check `jobs_state.json`
for its `cover_letter_path`/`resume_bullets_path`, or mark it
`interested`/`applied` with `set_status.py` to bring it back into the
Tracked section.

## HTML report

`report.py` renders `report.html` — a single self-contained,
mobile-friendly page: a pace-tracker banner (weekly/all-time applied
count) up top, then per job a score badge, clickable title linking
straight to the posting, company, location, category/probability tags,
salary/estimate, cost-of-living note, relocation-support flag, one-line
reason, trajectory callout, sibling links, cover letter + resume bullets
links, and status — styled for light and dark mode, no external
dependencies.

`match_jobs.py` regenerates `report.html` automatically at the end of
every run, after routing matches through `pipeline.process_run()`
(dedup → seen-job/state update → cover letter & salary-estimate backfill).

When no `ANTHROPIC_API_KEY` is available and scoring is instead done
manually (e.g. by Claude directly in a chat session): record raw
per-posting matches in `manual_matches.json` — including a real,
API-verified `salary` value per posting (never invented),
`category`/`probability`/`trajectory` per posting, and `relocation` per
posting (null unless the description actually says so — verify by
reading it, don't guess) — record any cover letter text / resume bullets
text / salary estimate figures for this run in `manual_extras.json`, then
run:

```
python3 apply_manual_scores.py
```

This goes through the same `pipeline.process_run()` and `write_report()`
as `match_jobs.py`, so `report.html` is produced identically regardless
of whether the matches came from a live run or a manual scoring pass.
