# job-agent

Job search tooling for clinical operations / quality / regulatory affairs
/ medical affairs / adjacent pharma-biotech leadership roles, plus
capacity-based matches in any other industry (large multi-country
programs, executive/named-client relationships, bid/proposal leadership,
50+ person distributed team oversight), workable from Brazil — remote,
or on-site/hybrid anywhere in the country. Manager-level and above only;
Senior Manager/Associate Director/Regional Director-equivalent scope is
the realistic primary target (the candidate's actual level), Director/VP/
Country Manager-equivalent scope is a tagged, separately-sorted "reach."
Candidate is based in Fortaleza. Code lives in `job-agent/`.

## "check jobs" shorthand

When the user says **"check jobs"**, treat it as the complete instruction
to do all of the following, without asking for confirmation:

1. Fetch current listings from every company board across all seven
   provider modules: `job-agent/fetch_greenhouse_jobs.py`,
   `job-agent/fetch_lever_jobs.py`, `job-agent/fetch_workable_jobs.py`,
   `job-agent/fetch_smartrecruiters_jobs.py`,
   `job-agent/fetch_ashby_jobs.py`, `job-agent/fetch_gupy_jobs.py`,
   `job-agent/fetch_workday_jobs.py` (each has its own `COMPANIES` dict;
   Ashby's is currently empty — see its module docstring/README for
   search notes before re-searching). `fetch_workday_jobs.py` now also
   covers non-pharma employers for the capacity-based search (Accenture,
   Kyndryl confirmed with real Brazil-based Director/Associate-Director/
   bid-leadership roles) — see its module docstring for companies checked
   and not found on any supported ATS. Its pharma/CRO tenants (IQVIA,
   Parexel, Syneos Health, ICON plc, Fortrea, **Thermo Fisher
   Scientific** — added as a *separate* Workday tenant from the
   Phenom-People-hosted jobs.thermofisher.com main site, confirmed with
   real Director/AD-level Program Management roles) fetch their **full**
   catalog rather than keyword-searching, and resolve any posting whose
   location collapses to an ambiguous "N Locations" summary — Workday's
   own full-text search is confirmed unreliable at surfacing every
   Brazil-eligible posting by search term alone (see
   `job-agent/fetch_workday_jobs.py`'s module docstring). Six of the
   seven (all but Gupy) are **international employers** hiring remotely
   into Brazil (tag every job they produce `"market": "International
   (remote)"`); Gupy covers **genuinely Brazilian-market employers**
   hiring locally in BRL (tag its jobs `"market": "Brazilian market
   (local)"`) — see `job-agent/README.md`'s "International vs. Brazilian
   market" and "Fetching listings" sections for the search methodology
   and exclusions (including Brazilian-native platforms checked and
   rejected for lacking a usable public feed: Catho, InfoJobs,
   Vagas.com; and CROs confirmed not on Workday: Medpace). Sibling-
   family mapping for dedup lives in `job-agent/companies.py`
   (`COMPANY_FAMILIES`), shared by all.

   **Title is a label on the result, never a filter before scoring.**
   Score every location-eligible posting (Brazil/LATAM-explicit, or an
   ambiguous/bare "Remote" location worth resolving) on its actual
   responsibilities and requirements — pull the full description before
   judging fit, the same way `match_jobs.py`'s `_is_location_eligible()`
   + pre-score description fetch now works when scoring via the API.
   This was a real, confirmed gap, not hypothetical: "Site Activation
   Manager" (IQVIA) and "Senior Site Navigator" (Fortrea) are both
   genuinely Brazil-eligible, Manager-level-or-above roles that a
   title-keyword read would skip, since neither title contains an
   obvious seniority/leadership word. When scoring manually (no API
   key), this means actually reading each Brazil-eligible posting's
   description before deciding it's out of scope — never excluding a
   posting from consideration on title wording alone.
2. Search for Director/Country Manager-level "stretch" leadership
   openings at major Brazilian pharma/healthcare employers — Aché, EMS,
   Hypera, Eurofarma (via Gupy where the company has a working board —
   see `job-agent/README.md`'s "Fetching listings" for confirmed
   subdomains and EMS's unconfirmed status) — plus a manual check of
   LinkedIn and Indeed. LinkedIn and Indeed are **not** automated
   providers: both explicitly disallow job-search scraping in
   `robots.txt`, so this step is a manual/WebSearch-assisted lookup each
   time, not a `fetch_*.py` script. Verify any candidate found is
   genuinely live before including it (LinkedIn search results
   frequently surface expired postings that 404 when opened directly —
   check before trusting a snippet). Tag any genuine match
   `"tier": "Stretch/Leadership"` (rendered as its own tag in the
   report, alongside category/probability/market) — separate from, and
   in addition to, the `level: "Reach"` tagging every Director/VP/
   Country-Manager-equivalent match gets regardless of source (see step
   4): `tier` marks a match as having come from this specific
   Director-level search sweep, `level` is the universal seniority
   classification applied to every match. It's normal and expected for
   this search to turn up nothing on a given run — director-level roles
   are typically filled through executive search rather than public
   postings — report that honestly ("checked, nothing open right now")
   rather than skipping the step silently or padding it with an
   unverified/stale listing.
3. **Open capacity search — not limited to the fixed company list.**
   Steps 1-2 only ever find postings at companies already enumerated in
   a `fetch_*.py` module's `COMPANIES` dict or Gupy's board list — a
   structural ceiling regardless of how good the scoring is. This step
   searches by capacity-defining *role type* instead, open to any
   company, any industry, anywhere in Brazil or remote-eligible:
   "Senior Program Manager," "Director of Program Management," "Head of
   PMO," "Portfolio Director," "Transformation Director," "VP Program
   Management" (combined with "Brazil"/"remote Brazil"/"LATAM" search
   terms). Like step 2, this is WebSearch-driven, not a `fetch_*.py`
   script — there's no structured API for an open, company-agnostic job
   search, so every candidate must be individually verified live
   (fetch the posting directly; don't trust a search snippet) before
   being scored. Score strictly on actual responsibilities — portfolio/
   program scope, $100M+ (ideally $200M+) budget oversight, matrix
   stakeholder management, bid-defense/client-relationship ownership,
   multi-country coordination — never on industry or title match; a
   genuine capacity match at a bank, logistics company, or tech firm
   counts exactly as much as one at a CRO. Tag any genuine match `"tier":
   "Capacity Search"` (its own tag in the report, same mechanism as
   `"Stretch/Leadership"` from step 2 — a match can't carry both tags
   since they mark different search origins, but both are independent of
   `level`, which still applies normally). As with step 2, a quiet run is
   expected and should be reported honestly, not padded.
4. Score each job for fit against `CANDIDATE_PROFILE` in
   `job-agent/match_jobs.py`, using the broadened rubric in
   `SCORING_INSTRUCTIONS`: not limited to an exact title match or to
   pharma/CRO employers. Two overlapping lanes are in scope: (a) clinical
   operations, quality, regulatory affairs, medical affairs, or other
   pharma/biotech leadership functions where trial/portfolio management
   experience is a strong transferable fit; (b) capacity-based matches in
   ANY other industry — large multi-country program management ($100M+
   scope), executive/named-client relationship ownership, bid/proposal
   leadership, or 50+ person distributed team oversight — the sector
   doesn't matter, the actual scope/seniority demands do. Prioritize
   compensation and long-term career trajectory over exact title wording.

   Hard requirements, not traded off:
   - Workable from Brazil — either explicitly remote/LATAM-inclusive, or
     physically on-site/hybrid anywhere in Brazil (cap at 40 otherwise).
   - Manager-level or above only. Never surface individual-contributor,
     analyst, associate, or specialist/consultant-titled roles even when
     the function is a strong fit (cap at 30) — a "Coordenador"/
     "Coordinator" title with genuine site/team leadership scope, not
     just individual task execution, is the one judged-by-real-scope
     exception, same as the existing Brazilian-market-title-convention
     note below.
   - Level calibration matches the candidate's actual level (5.5 years,
     fast trajectory, no prior Director title), not aspiration: Senior
     Manager, Associate Director, and Regional Director (or equivalent
     scope in non-pharma industries) are the realistic primary target,
     scored normally. Full Director, VP, Country Manager, or higher (or
     equivalent scope) get `level: "Reach"` regardless of score, and lean
     toward "Long-shot" probability unless the specific posting's actual
     requirements (not just the title) plausibly fit 5.5 years of
     experience.

   For Director/Country Manager-level and other client-facing or
   business-development-adjacent roles specifically (whether "Reach" or
   not), weigh the candidate's sponsor-facing and commercial credibility
   explicitly: representing Labcorp internationally to a major sponsor
   (Novartis), regular client audit participation, and 4 bid defenses are
   exactly what these roles screen for. The candidate is trilingual
   (English C2, Portuguese C2, German B1) — factor this in specifically,
   beyond the baseline Brazil-eligibility requirement, for roles that
   explicitly span EMEA/LATAM or explicitly value multilingual
   client-facing work.

   Also assign, per job: `category` ("In-field" direct clinical-ops/
   trial-management work, or "Adjacent" transferable-skills fit
   elsewhere, including non-pharma capacity-based matches), `level`
   ("Primary" or "Reach", per the calibration above), `probability`
   ("High"/"Medium"/"Long-shot" — a realistic, not encouraging-by-default
   read on how closely actual experience maps to what's likely required),
   `trajectory` (one line: lateral/step-up/bigger-leap versus the
   candidate's current role, and whether it's worth pursuing as a
   stretch), and `relocation` (relocation assistance / home-office
   stipend / sign-on bonus, only if the posting's own text says so —
   blank, never guessed, otherwise). For Brazilian-market (Gupy) postings,
   read titles by local convention, not literal US-title equivalence
   (e.g. "Coordenador" is typically genuine site/operational-leadership
   scope locally, not a junior title) — but still score honestly: most
   currently-open local roles are individual-contributor ("Analista")
   level (now excluded entirely under the Manager-level floor above), and
   any real step-down in scope/pay from the candidate's Portfolio Manager
   role that a surfaced match does carry belongs in the score and
   `trajectory` line rather than being smoothed over.
   - If `ANTHROPIC_API_KEY` is set, run `python3 match_jobs.py` — it
     fetches, scores, and runs the full pipeline (below) itself.
   - If no API key is available, score manually (as Claude, in
     conversation) using the same rubric, record raw per-posting matches
     in `job-agent/manual_matches.json` (with a real, API-verified
     `salary` per posting — see step 5, never invented — plus
     `category`/`probability`/`trajectory`/`market` per posting), record
     any cover letter / resume bullets text / salary estimate figures for
     this run in `job-agent/manual_extras.json`, then run
     `python3 apply_manual_scores.py`.
5. The pipeline (`job-agent/pipeline.py`, used identically by both paths
   above) then:
   - **Dedupes sibling postings** (`job-agent/dedup.py`): the same role
     posted on multiple boards from the same corporate family (per
     `COMPANY_FAMILIES`, e.g. Precision Medicine Group / Precision for
     Medicine / Precision AQ) is shown once, with other boards' links
     noted.
   - **Tracks seen jobs** (`job-agent/jobs_state.py`,
     `job-agent/jobs_state.json`): only matches new since the last check
     are surfaced as "New matches" in the report. Anything the user has
     marked `interested`, `applied`, or `interviewing` (via
     `set_status.py`) stays visible in its own section ("Interested" or
     "Applied") regardless of whether it's new this run — see "Job status
     model" below. A match that scored 60+ before and was never actioned
     does not resurface in "New matches" — don't re-show the same jobs
     every day there. But **nothing tracked is ever silently dropped from
     the report as a whole**: every match ever scored 60+, regardless of
     status (including `declined`/`pass`, visibly tagged rather than
     hidden), stays permanently visible in the "All Matches Archive"
     section at the bottom of every report — see "Job status model"
     below. A job's only way out of view entirely is not being tracked at
     all.
   - **Checks every tracked posting's live link** (`job-agent/link_check.py`,
     called by `job-agent/pipeline.py`'s `check_expired_links()`): this is
     a separate check on *existing* tracked matches, not on new fetches —
     re-requests each job's primary URL and flags `link_status: "expired"`
     if it now 404s/410s or redirects to the job board's own "not found"
     page (a plain status-code check isn't enough — Greenhouse in
     particular 200s a dead job URL, redirecting to the board root with
     `?error=true`, so the check also inspects the final URL and page
     text for known "gone" signals). A network failure (timeout, DNS)
     never flips a posting to expired — that returns "unknown" and the
     prior status is left alone, since a transient failure isn't evidence
     the posting is gone. Expired postings stay visible in the report
     (never silently removed) but get a "⚠ Expired" tag and a muted,
     struck-through card so they read as likely filled/pulled; they're
     also skipped for cover letter/resume bullet drafting going forward.
     Declined/passed jobs aren't checked (the user's already done with
     those).
   - **Drafts cover letters and resume bullet adjustments** for any match
     scoring 80+ that doesn't have them yet (`job-agent/cover_letter.py`,
     `job-agent/resume_bullets.py`), saved to
     `job-agent/cover_letters/<slug>.md` and
     `job-agent/resume_bullets/<slug>.md` for the user to review/edit —
     never auto-submitted anywhere. Resume bullets are 3-4 rewritten
     bullets pulling only from `CANDIDATE_PROFILE`'s real experience,
     reordered/emphasized for the specific role — never inventing new
     accomplishments or numbers. The two backfill independently, so an
     existing cover letter doesn't block generating missing bullets (or
     vice versa).
   - **Estimates salary** when a posting doesn't disclose one
     (`job-agent/salary_estimate.py`): a rough, clearly-labeled
     market-rate range (e.g. "~$60,000–$90,000 USD (estimated — ...,
     not disclosed by employer)"), distinct from a real disclosed figure
     from `job-agent/salary.py` (which only ever reports a number when
     the posting structurally discloses one — metadata field or embedded
     pay-transparency widget — never inferred from other figures in the
     description). Brazilian-market (Gupy) postings never structurally
     disclose salary at all, so they always go through
     `job-agent/br_salary_estimate.py` instead — a title-matched table of
     monthly BRL ranges grounded in real Glassdoor Brasil reference data
     per title cluster (not pure inference), e.g. "R$6.800–R$10.500/month
     (estimated — Glassdoor Brazil, Analista de Pesquisa Clínica Sênior,
     not disclosed by employer)".
   - **Tags every posting's pay figure with a `salary_confidence`**:
     `"confirmed"` (real disclosed pay found for this exact role/company —
     set automatically whenever `salary` is structurally disclosed, never
     hand-set otherwise), `"estimated"` (an estimate with no real data
     contradicting it — the default, and not a strike against a posting),
     or `"flagged"` (an estimate where a real, specific contradicting data
     point turned up — e.g. a disclosed comparable role's pay converting
     to well below the estimate, or a title falling back to a
     loosely-grounded generic band — never applied just for being
     unverified, and never used for a functional/scope mismatch, which
     belongs in the fit reasoning text instead). Shown as its own badge
     next to the score on every card — never buried in the description
     text. Score remains the primary sort driver within every group;
     `salary_confidence` only nudges it — `"confirmed"` gets a modest
     +3-5 point boost since it's real disclosed money, `"flagged"` gets a
     real -10-15 point penalty, `"estimated"` gets no adjustment. This is
     a nudge, not a tier override: a flagged 95 can still outrank a
     confirmed 80.
   - **Adds a city + cost-of-living note** (`job-agent/cost_of_living.py`):
     extracts the specific city from the location when one is named
     (blank for bare "Remote, Brazil" postings), and — when a salary
     figure (disclosed or estimated) is available — a plain-language,
     clearly-labeled-as-rough comparison against Fortaleza (the
     candidate's home base), e.g. "São Paulo's cost of living runs
     roughly 45% higher than Fortaleza... R$325.000–R$475.000 there is
     roughly equivalent to R$224.000–R$328.000 of purchasing power in
     Fortaleza." International (USD) matches convert through an
     approximate FX rate first (`col_comparison_note`); Brazilian-market
     matches are already monthly BRL, so no FX step is needed
     (`col_comparison_note_brl`). Computed deterministically (no API
     call) on every run.
6. Update `job-agent/report.html` with the fresh matches (score 60+,
   "New matches" / "Applied" / "Interested" sections, plus the "All
   Matches Archive" section that always shows every tracked match
   regardless of status — see "Job status model" below — each showing a
   market tag ("International (remote)" / "Brazilian market (local)"), a
   Stretch/Leadership tag on any job tagged that way in step 2, a
   Capacity Search tag on any job tagged that way in step 3, a
   "Reach — Long Shot" tag on any job with
   `level: "Reach"`, category/probability tags, a `salary_confidence`
   badge (Confirmed/Estimated/Flagged) shown plainly next to the score,
   salary/estimate, cost-of-living note, relocation-support flag, a
   trajectory callout, sibling links, status, and cover letter/resume
   bullets links where applicable) — this happens automatically via
   `report.write_report()` in both paths above. Within each section,
   whenever both `level: "Primary"` and `level: "Reach"` matches are
   present, Reach matches are sorted into their own labeled block at the
   bottom, separate from and below the realistic Primary matches — never
   interleaved by score alone. Within every such group, cards are sorted
   by score, nudged by `salary_confidence` (Confirmed +3-5, Flagged
   -10-15, Estimated unchanged) rather than a hard confidence-tier
   override — a Flagged 95 can still outrank a Confirmed 80. Whenever a
   group (Primary or Reach) contains both
   markets, it's split into two labeled subsections so international and
   Brazilian-market results can be compared side by side rather than
   interleaved by score.
   Note: draft links only render for jobs currently in one of those
   sections — a job that already has drafts but has scrolled out of "new"
   (seen before, no status set) still has the files in the repo, just not
   linked from the report until it's marked `interested`/`applied`/
   `interviewing`.
7. `report.html` must keep every job title as its own clickable link
   straight to the (primary) posting, and its header must show, every
   time the report is generated: the pace tracker (a running "N applied
   this week · M all-time" count from
   `job-agent/applications_log.json`, via `job-agent/pace_tracker.py`,
   logged automatically whenever `set_status.py <url> applied` or
   `interviewing` is run); a clear applied-vs-total count ("N applied of
   M total matches tracked", computed from every job ever recorded in
   `job-agent/jobs_state.json` regardless of status — not just this
   run's visible cards) so progress is visible even on a run with zero
   new matches; and a one-line reminder of what `set_status.py` actually
   does. This reminder belongs in the report itself (so it's visible
   every time, not just when asked) via `report.generate_report_html()`.
   Every card also carries status buttons (`Mark applied` / `Mark
   interviewing` / `Mark interested` / `Decline`) that copy that job's
   exact `set_status.py <url> <status>` command to the clipboard —
   `report.html` has no backend, so this can't write to
   `jobs_state.json` on its own; it only removes the friction of finding
   the URL. Be upfront about that limit if asked for a "real" checkbox.
8. Summarize the results back to the user (what's new since last time,
   any status changes reflected, any cover letters/resume bullets
   drafted, and — if steps 2/3 found anything — the stretch/leadership
   and open-capacity-search results) and mention the updated report.

## Job status model

Each tracked job has a `status`: `new` (default), `interested`,
`applied`, `interviewing`, `declined`, or `pass`. `set_status.py <url>
<status>` sets it:
- `new` / `interested`: `new` shows in "New matches" until acted on;
  `interested` moves it to its own "Interested" section.
- `applied` / `interviewing`: both show together in "Applied" —
  `interviewing` is a later stage of the same active application, not a
  separate track, but is flagged distinctly on the card (bold title,
  purple border/tag) so in-progress interviews stand out from a plain
  "applied and waiting" posting. Both log to the pace tracker (once per
  job — jumping straight to `interviewing` without ever setting
  `applied` still counts correctly).
- `declined` / `pass`: both exclude the job from every *active* section
  ("New matches"/"Interested"/"Applied") — including if the same
  posting is re-fetched on a later run, since an existing key's status
  is never overwritten by a re-fetch, only its live fields like
  score/salary are. They do **not**, however, remove the job from the
  report entirely: it stays visible in the "All Matches Archive"
  section, tagged "Declined"/"Passed" and shown at reduced opacity, so
  the user can always find it again (including to reverse the decision
  via `set_status.py <url> new`/`interested`) rather than losing it for
  good. `declined` and `pass` are otherwise interchangeable; `declined`
  exists as the more natural word for "this specific application didn't
  work out" versus `pass`'s "not interested in the first place."

Every match ever scored 60+, regardless of status, is permanently
visible somewhere in the report — see the "All Matches Archive" section
(`report.py`'s `generate_report_html()`, sorted the same
confidence-nudged-by-score way as every other section, with the same
Primary/Reach and market splits). A posting whose live status changes
(link goes dead, salary gets reassessed) is flagged in place on its
existing entry — `link_status`/`salary_confidence` update the same
tracked record — never deleted and re-added. The only way a job stops
appearing anywhere in the report is if it stops being tracked at all
(which nothing in this pipeline currently does).

See `job-agent/README.md` for full details on each script.
