# job-agent

Tools for finding clinical operations / quality / regulatory affairs /
medical affairs / adjacent pharma-biotech leadership roles workable from
Brazil — remote, or on-site/hybrid anywhere in the country. Candidate is
based in Fortaleza.

## Fetching listings

Seven provider modules, one per ATS, all with the same shape (`COMPANIES`
dict of token → display name, plus a `fetch_jobs()`). Six of the seven
(all but Gupy) cover **international employers** hiring remotely into
Brazil (or Brazil/LATAM job boards of foreign-HQ CROs/biotechs); Gupy
covers **genuinely Brazilian-market employers** hiring locally in BRL —
see "International vs. Brazilian market" below.

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
- `fetch_gupy_jobs.py` — Gupy boards (Brazil's dominant recruiting
  platform, used by genuinely **Brazilian-market** employers — see
  "International vs. Brazilian market" below):
  - **Synvia** — dedicated Brazilian CRO, the largest/most relevant hit
    for clinical operations
  - **IDOR** (Instituto D'Or de Pesquisa e Ensino) — Rede D'Or's research
    institute
  - **Eurofarma** — major Brazilian pharma
  - **Rennova** — aesthetics/medical products company with a clinical
    research function (no clinical-ops-relevant postings as of this
    check, kept tracked)
  - **Aché** (subdomain `vagasache`) — major Brazilian pharma, added for
    the Director/Country Manager stretch/leadership search (see below)
  - **Hypera Pharma** (subdomain `hyperapharma`) — major Brazilian
    pharma, added for the same reason
  - **EMS Farmacêutica** — could **not** confirm a working subdomain.
    `ems.gupy.io` returns a genuine Gupy-hosted 404 (not a DNS failure),
    and plausible alternates (`emsfarmaceutica`, `gruponc`, `vagasems`,
    etc.) also 404, despite several secondary sources naming
    `ems.gupy.io` as correct — possibly a recently deactivated/migrated
    board. Not in `COMPANIES`; worth re-checking on a future search.
  Gupy has no documented public read API — `developers.gupy.io` covers
  only the authenticated employer-side API. Company career pages
  (`https://{company}.gupy.io/`) are public and server-render the full
  open-job list into a Next.js `__NEXT_DATA__` script tag; the job detail
  page (`.../jobs/{id}`) does the same for description/prerequisites/
  responsibilities text (not present on the list-page job objects). Both
  are read the same way any visitor's browser would, unauthenticated —
  same principle as the other providers' public JSON APIs.
- `fetch_workday_jobs.py` — Workday-hosted career sites. Originally built
  for major CROs missing from every other provider, later extended to
  large non-pharma employers for the capacity-based (industry-agnostic)
  search — see "Industry scope" below:
  - Pharma/CRO: **IQVIA**, **Parexel**, **Syneos Health**, **ICON plc**,
    **Fortrea**
  - Non-pharma: **Accenture**, **Kyndryl** (IBM's IT-infrastructure
    spinoff) — confirmed with real São Paulo/Rio-based Director/
    Associate-Director/bid-proposal-leadership roles
  Workday exposes a public, unauthenticated JSON search API per tenant at
  `https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`
  (POST), plus a matching per-job detail endpoint at
  `.../job{externalPath}` (GET) — verified directly (curled and confirmed
  real job data, same as every other provider) before committing to this
  provider, per the same standard used for Greenhouse/Lever originally.
  Each tenant's facet configuration differs (IQVIA exposes a
  `Location_Country` facet; most others don't), so rather than depend on
  facets, `fetch_jobs()` searches Workday's full-text `searchText` per
  tenant, merging results (deduped by `externalPath`). Pharma CRO boards
  run 300-1,800+ total postings; Accenture/Kyndryl run into the
  thousands across every function and seniority level, so their search
  terms (`search_terms` per tenant in `_TENANTS`, see the module) combine
  a location signal with a seniority/capacity signal (e.g. `"Sao Paulo
  Director"`, `"Propostas Comerciais"`) rather than relying on location
  text alone — fetching everything and filtering client-side, as the
  smaller providers do, isn't practical at this scale.
  - **Medpace** — uses iCIMS (`uscareers-medpace.icims.com`), confirmed
    **not** on Workday.
  - **PPD** (the clinical-research business of Thermo Fisher Scientific)
    — uses Phenom People (`jobs.thermofisher.com`), the same platform
    already noted as a dead end for standalone Thermo Fisher above,
    confirmed **not** on Workday.
  - Checked for a public ATS on any provider this pipeline supports (not
    just Workday) and **not found** — most run custom/proprietary career
    portals: Globant, EPAM Systems, Endava, Capgemini, DXC Technology,
    NTT Data, Cognizant, Wipro, Infosys, TCS, IBM, AECOM, Jacobs
    Engineering, WSP Global, Fluor, Bechtel.
  - **TELUS Digital Brazil** has a Greenhouse board (`telusdigitalbr`)
    but no live postings as of this check.
  - **Thoughtworks** is on Greenhouse (confirmed, 46 jobs) but none are
    Brazil-eligible/senior enough as of this check.

**Brazilian-native job platforms checked and rejected as providers**
(Catho, InfoJobs, Vagas.com): none exposes a usable public API or
structured feed, unlike Gupy. Verified directly rather than assumed —
fetched each site's search-results HTML and checked for `__NEXT_DATA__`,
JobPosting JSON-LD, or any embedded JSON: all three are pure
server-rendered HTML with none of those. Vagas.com's `.rss`/`.xml` URL
suffixes return HTTP 200, which looked promising, but both just fall
through to the same HTML search page (the suffix gets treated as part of
the search term, not a format extension) — not a real feed. Building a
provider for any of these would mean HTML scraping, a materially more
fragile approach than every other provider in this pipeline (all of
which rely on structured JSON) — deliberately not built for that reason.
If one of these sites adds a real API/feed later, it's worth revisiting.

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
python3 fetch_gupy_jobs.py
python3 fetch_workday_jobs.py
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

*Gupy* — companies checked and ruled out: Rede D'Or's main job board
(1,600+ openings, but overwhelmingly clinical-engineering/patient-care
roles, not clinical-trial work — its dedicated research institute, IDOR,
is the relevant board instead), Hospital Santa Lucinda (too small, ~6
open roles, none relevant), a deactivated "icts" group board (0 jobs),
PUCRS (0 currently-open relevant roles). Cristália and Hypera Pharma are
real major Brazilian pharma companies but their current Gupy postings are
pharma R&D/QC/manufacturing, not clinical operations — deprioritized, not
excluded outright; worth rechecking later. Within each company's board,
lab-technician, nursing, finance, quality-control, and pre-clinical-R&D
titles are filtered out as out-of-scope function even when they mention
"pesquisa clínica" in passing.

## International vs. Brazilian market

Every match carries a `market` field: `"International (remote)"` (the
first five providers — foreign-HQ employers reaching into Brazil via
remote/PEO arrangements, generally paying USD) or `"Brazilian market
(local)"` (Gupy — genuinely Brazilian employers hiring locally, paying
BRL at local market rates). `report.html` tags every card with its market
and, whenever a "New matches" or "Tracked" section contains both, splits
it into two labeled subsections so the two can be compared side by side
rather than interleaved by score.

Because Gupy postings never structurally disclose salary at all (no
Brazilian ATS in this pipeline exposes a pay field), Brazilian-market
matches always go through the salary-estimate fallback below, and their
estimates are BRL-denominated and monthly (the normal way Brazilian
salaries are quoted), not USD/annual like the international estimates.

Brazilian CRO/pharma title conventions differ from US ones and are
scored accordingly rather than read literally: e.g. "Coordenador" is
typically a genuine site/operational-leadership role locally, not a
junior title, even though it still sits well below the candidate's
current portfolio-management scope. Scores for this market honestly
reflect that most currently-open roles are individual-contributor
("Analista") level — a real step down in scope and pay from the
candidate's Portfolio Manager role — while still surfacing the strongest
options (site/study coordination, senior specialist roles) as legitimate
local-market footholds rather than inflating or zeroing them out
wholesale.

## Stretch/leadership search

Alongside the regular clinical-ops/quality/regulatory/medical-affairs
matching, each run also searches specifically for Director/Country
Manager-level pharma/healthcare openings — a deliberately higher-reach
"stretch" search rather than a close functional-fit search. Any genuine
match gets `"tier": "Stretch/Leadership"`, rendered as its own tag on
the report card (alongside market/category/probability).

Two sources:
- **Gupy** (automated): Aché, EMS (unconfirmed — see above), Hypera
  Pharma, and Eurofarma's full job lists (not just the clinical-ops
  subset) are scanned for Director/Country Manager/VP-level titles at
  scoring time, same mechanism as every other Gupy search.
- **LinkedIn and Indeed** (manual, every run): both explicitly disallow
  job-search scraping in `robots.txt` (`Disallow: /jobs?runSearch*`,
  `/jobs-guest/`, `/api/jobPostings/jobs*` on LinkedIn; similar on
  Indeed), so this is a WebSearch-assisted manual lookup each time, not
  an automated `fetch_*.py` provider — and isn't going to become one.
  Verify a candidate is actually live before including it: search
  results for both sites frequently surface expired listings (one
  checked while building this feature was a real-looking "Director,
  Clinical Operations" posting whose direct URL 404'd) — never include
  one without opening the direct link and confirming it's still posted.

It's normal and expected for this search to come up empty on a given
run — checked at launch across Aché, Hypera Pharma, and Eurofarma's
full Gupy boards (title-scanned in full, not just keyword-filtered) plus
a LinkedIn/Indeed pass, and found zero genuinely open Director/Country
Manager roles at any of them. Director-level pharma hires in Brazil are
typically filled through executive search firms/headhunters rather than
posted on public job boards, which is the likely explanation. Report
this honestly ("checked, nothing open") rather than skipping the step
or padding it with a stale/unverified listing.

## Industry scope (capacity-based matches)

Alongside pharma/CRO matching, each run also searches for capacity-based
matches in any other industry: large multi-country program management
($100M+ scope), executive/named-client relationship ownership, bid/
proposal leadership, or 50+ person distributed team oversight. The
sector doesn't matter — what matters is whether the role's actual scope
and seniority demands match what the candidate already does. This is a
separate mechanism from the pharma-specific stretch/leadership search
above (which stays scoped to Gupy pharma companies + LinkedIn/Indeed);
industry-broadened matches come through `fetch_workday_jobs.py`'s
non-pharma tenants (Accenture, Kyndryl — see "Fetching listings" above
for the full list of companies checked and not found on a public ATS).

Found 5 genuine matches on the first pass: an Associate Director role at
Accenture (Talent & Organization, explicitly combining C-level client
relationships with technical/commercial proposal leadership), two
Accenture bid/proposal-management roles in Rio de Janeiro, and two
Kyndryl account-leadership roles in São Paulo (one Director-level, one
senior-manager-level). All scored `category: "Adjacent"` (non-pharma
function) and honestly reflect that this is a genuine industry pivot —
`probability` stays "Medium" even for strong capacity matches, since
domain knowledge in the new industry is untested, not just the
transferable skills.

## Level calibration (Primary vs Reach)

Every match gets a `level`: `"Primary"` or `"Reach"`, reflecting the
candidate's actual level (5.5 years of progressively senior experience,
fast trajectory, but no prior Director-level title) rather than
aspiration:
- **Primary** — Senior Manager, Associate Director, or Regional
  Director-equivalent scope (in pharma or the broadened industries
  above). This is the realistic target band and where most matches
  should land.
- **Reach** — full Director, VP, Country Manager, or higher-equivalent
  scope. Kept visible (never filtered out), but tagged "Reach — Long
  Shot" on the card and sorted into its own labeled block at the bottom
  of each report section (`report._section()`), below the Primary
  matches — never interleaved by score alone. `probability` leans
  "Long-shot" for these unless the specific posting's actual
  requirements (not just the title) plausibly fit 5.5 years of
  experience — a strong fit narrative doesn't override the level gap.

A hard Manager-level floor applies underneath both bands: individual-
contributor, analyst, associate, and specialist/consultant-titled roles
are excluded entirely, even when the function is a strong fit (this
removed 20 previously-surfaced matches in one pass when the floor was
introduced — Analista/Especialista-titled Gupy roles, Lead Clinical
Research Associate, Senior Clinical QA Specialist, MSL, TMF Lead II,
and similar). The one scope-over-title exception: a "Coordenador"/
"Coordinator"-titled role that genuinely carries site/team leadership,
not just individual task execution, is judged on that real scope —
consistent with the Brazilian-market title-convention note above.

## Resume-based matching

`match_jobs.py` fetches jobs from every company across all seven
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
anything else is capped at 40 regardless of functional fit.
`SCORING_INSTRUCTIONS` also explicitly calls out weighing the
candidate's real sponsor-facing/commercial credentials (Global Study
Manager on Novartis's largest Labcorp trial, direct international
client representation, bid-defense participation) for Director/Country
Manager-level and other client-facing or business-development-adjacent
roles specifically, since that's distinct from — and beyond — pure
operational/trial-management scope. See `SCORING_INSTRUCTIONS` and
`CANDIDATE_PROFILE` in `match_jobs.py` for the exact prompt/background
text.

## Category, probability, and trajectory

Alongside the score/reason, each match also gets four more fields (from
the same Claude scoring call, or filled in manually in
`manual_matches.json` on the manual path):
- **category** — `"In-field"` (direct clinical operations/trial
  management work) or `"Adjacent"` (transferable-skills fit elsewhere —
  regulatory, quality, program/portfolio leadership outside pharma,
  general operations, non-pharma capacity-based matches, etc.).
- **level** — `"Primary"` or `"Reach"`, per "Level calibration" above.
- **probability** — `"High"`, `"Medium"`, or `"Long-shot"`, a realistic
  (not encouraging-by-default) read on how closely the candidate's actual
  experience maps to what the role likely requires — seniority, domain
  depth, therapeutic-area fit, language/region fit, etc. A role that
  *sounds* senior but needs deep therapeutic-area-specific experience the
  candidate doesn't have (e.g. a Gastroenterology-specific leadership
  role, when the candidate's therapeutic background is Oncology/
  Autoimmune/Malaria) should score as `"Long-shot"` even if the title fit
  looks strong. `level: "Reach"` matches lean "Long-shot" for the same
  reason unless the posting's actual requirements plausibly fit 5.5
  years of experience.
- **trajectory** — one line on whether the role is a lateral move, a step
  up, or a bigger leap versus the candidate's current role, plus a
  plain-spoken read on whether it's worth pursuing even as a stretch.

The candidate is trilingual (English C2, Portuguese C2, German B1);
`SCORING_INSTRUCTIONS` calls this out as a specific, weighted factor —
not just generic language skill — for roles that explicitly span EMEA/
LATAM or explicitly value multilingual client-facing work, beyond the
baseline Brazil-eligibility requirement every match already needs.

These render as colored tags (category/level/probability) and a bordered
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
`applied`, `interviewing`, `declined`, or `pass`. Set it with:

```
python3 set_status.py <posting-url> applied|interested|interviewing|declined|pass
```

(any of a job's apply links works, even after dedup). `report.html`
shows three sections:
- **New matches** — first time crossing 60+ this run, status still `new`.
- **Applied** — anything marked `applied` or `interviewing`. Both share
  this section since `interviewing` is a later stage of the same active
  application, not a separate track, but an `interviewing` card is
  flagged distinctly (bold title, purple border and tag) so you can see
  what's actively progressing versus a plain "applied and waiting"
  posting at a glance.
- **Interested** — anything marked `interested`, kept separate from
  Applied so you can distinguish "still deciding" from "actually in
  process."

`applied` and `interviewing` both log to `pace_tracker.py` (once per
job, deduped by key) — so marking something `interviewing` directly,
without ever setting `applied` first, still counts correctly toward the
weekly/all-time pace stats and the header's applied-vs-total count.

Jobs marked `declined` or `pass` are hidden from the report entirely
(they stay in `jobs_state.json` for the record, just filtered out of
every rendered section) — and **permanently**: once a job's key exists
in state, `update_state()` only ever refreshes its live fields
(score/salary/location/etc.) on a later fetch, never its status, so a
`declined`/`pass` job can't silently resurface as `new` even if the
exact same posting is re-fetched on a future run. `declined` and `pass`
behave identically; `declined` just reads more naturally for "I applied
and it didn't work out" versus `pass`'s "not interested to begin with."

Re-run `match_jobs.py` / `apply_manual_scores.py` after changing a status
to refresh the report.

**Updating status from the report itself:** `report.html` is a static
generated file with no backend, so it can't write to `jobs_state.json`
directly — there's no real "tick" that persists a status change on its
own. What it does have: every card carries status buttons (`Mark
applied` / `Mark interviewing` / `Mark interested` / `Decline`) that
copy the exact `set_status.py` command for that specific job — URL
already filled in — to your clipboard via a small inline script (vanilla
JS, `navigator.clipboard`, with a `window.prompt()` fallback if
clipboard access is blocked, e.g. some `file://` contexts). Click a
button, paste into a terminal, run it, then re-run
`apply_manual_scores.py` / `match_jobs.py` to see it reflected. This
removes the friction of hunting down the URL yourself, but the actual
status change still requires running the command — the report cannot
update itself.

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
- Workday (`extract_salary_workday()`) — a pay-transparency disclosure in
  the job description body text, matched only when an explicit "salary
  range"/"pay range"/"base salary range"/"compensation range" label
  immediately precedes two dollar figures (the format US state
  pay-transparency laws require, e.g. `"Salary Range: $95,000.00 -
  $175,700.00"`) — not any other dollar figure in the description, and
  not generic "competitive salary" boilerplate that mentions the word
  "salary" without a number. Requires a per-job detail fetch (the search
  endpoint doesn't include the description).

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

Brazilian-market (Gupy) matches use `br_salary_estimate.py` instead,
since Gupy never structurally discloses a salary field at all. Rather
than a fresh model guess each run, it's a small title-keyword-matched
table of monthly BRL ranges grounded in real Glassdoor Brasil salary
pages researched per title cluster (Gerente/Coordenador de Pesquisa
Clínica, Monitor/CRA, Farmacovigilância, Assuntos Regulatórios, Data
Management, etc. — see `_BANDS` in `br_salary_estimate.py`, each entry
citing its source), rather than pure inference — those sites require a
browser session and block simple scraping, so this is a snapshot revisit
if the market moves noticeably rather than a live scrape on every run.
Brazilian titles abbreviate "sênior" as "Sr" at least as often as
spelling it out, so seniority-band matching checks for both. Output is
always monthly BRL (e.g. `"R$6.800–R$10.500/month (estimated — Glassdoor
Brazil, Analista de Pesquisa Clínica Sênior, not disclosed by employer)"`)
— never annualized, matching Brazilian salary-quoting convention.

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

`pace_tracker.py` logs every job marked `applied` or `interviewing`
(once per job, even if re-marked or marked with both over time) to
`applications_log.json`, timestamped. `set_status.py` calls
`log_application()` automatically whenever you run `set_status.py <url>
applied` or `interviewing` — so jumping straight to `interviewing`
without ever setting `applied` first still counts correctly.
`report.html`'s header shows a running "N applied this week · M
all-time" count, computed fresh from the log on every report generation
— meant as a simple, durable way to see pace toward an active search
over the coming year, not a specific numeric goal (none was set).

The header also shows a second, distinct count: "N applied of M total
matches tracked", computed directly from `jobs_state.json` (every job
ever recorded, regardless of current status) rather than from the pace
log — this stays meaningful even on a run with zero new matches or zero
applications this week, since `total_tracked` doesn't depend on what's
currently visible in the New/Applied/Interested sections. Right below
it, a one-line reminder spells out what each status actually does. This
reminder is baked into `report.generate_report_html()` itself, so it
renders on every report regardless of whether anyone asks — not just
something mentioned in chat once.

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

Brazilian-market matches skip the FX step entirely — their salary/
estimate figures are already monthly BRL, so `col_comparison_note_brl()`
just applies the COL ratio directly (`pipeline.py` branches on the job's
`market` field to pick the right path, parsing the BRL "R$X.XXX" figures
with `parse_brl_salary_figures()` rather than the USD parser).

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
