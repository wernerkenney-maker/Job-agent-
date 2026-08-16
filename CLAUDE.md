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
   and not found on any supported ATS. Six of the seven (all but Gupy) are
   **international employers** hiring remotely into Brazil (tag every job
   they produce `"market": "International (remote)"`); Gupy covers
   **genuinely Brazilian-market employers** hiring locally in BRL (tag
   its jobs `"market": "Brazilian market (local)"`) — see
   `job-agent/README.md`'s "International vs. Brazilian market" and
   "Fetching listings" sections for the search methodology and
   exclusions (including Brazilian-native platforms checked and rejected
   for lacking a usable public feed: Catho, InfoJobs, Vagas.com; and CROs
   confirmed not on Workday: Medpace, PPD/Thermo Fisher). Sibling-
   family mapping for dedup lives in `job-agent/companies.py`
   (`COMPANY_FAMILIES`), shared by all.
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
   3): `tier` marks a match as having come from this specific
   Director-level search sweep, `level` is the universal seniority
   classification applied to every match. It's normal and expected for
   this search to turn up nothing on a given run — director-level roles
   are typically filled through executive search rather than public
   postings — report that honestly ("checked, nothing open right now")
   rather than skipping the step silently or padding it with an
   unverified/stale listing.
3. Score each job for fit against `CANDIDATE_PROFILE` in
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
     `salary` per posting — see step 4, never invented — plus
     `category`/`probability`/`trajectory`/`market` per posting), record
     any cover letter / resume bullets text / salary estimate figures for
     this run in `job-agent/manual_extras.json`, then run
     `python3 apply_manual_scores.py`.
4. The pipeline (`job-agent/pipeline.py`, used identically by both paths
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
     model" below. Anything marked `declined` or `pass` is hidden from
     the report entirely, permanently. A match that scored 60+ before and
     was never actioned does not resurface — don't re-show the same jobs
     every day.
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
     contradicting it — the default), or `"flagged"` (an estimate where
     real reference data turned up a signal that it may be significantly
     off, e.g. a title falling back to a loosely-grounded generic band
     rather than a specific title-matched one). Shown as its own badge
     next to the score on every card — never buried in the description
     text. Sort order within every group is `salary_confidence` first
     (Confirmed, then Estimated, then Flagged) and score second, so a
     Confirmed 90 ranks above a Flagged 95.
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
5. Update `job-agent/report.html` with the fresh matches (score 60+,
   "New matches" / "Applied" / "Interested" sections — see "Job status
   model" below — each showing a market tag ("International (remote)" /
   "Brazilian market (local)"), a Stretch/Leadership tag on any job
   tagged that way in step 2, a "Reach — Long Shot" tag on any job with
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
   by `salary_confidence` first and score second (a Confirmed 90 ranks
   above a Flagged 95). Whenever a group (Primary or Reach) contains both
   markets, it's split into two labeled subsections so international and
   Brazilian-market results can be compared side by side rather than
   interleaved by score.
   Note: draft links only render for jobs currently in one of those
   sections — a job that already has drafts but has scrolled out of "new"
   (seen before, no status set) still has the files in the repo, just not
   linked from the report until it's marked `interested`/`applied`/
   `interviewing`.
6. `report.html` must keep every job title as its own clickable link
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
7. Summarize the results back to the user (what's new since last time,
   any status changes reflected, any cover letters/resume bullets
   drafted, and — if step 2 found anything — the stretch/leadership
   result) and mention the updated report.

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
- `declined` / `pass`: both permanently exclude the job from every
  future report section, including if the same posting is re-fetched on
  a later run — this falls out of `jobs_state.py`'s existing
  seen-job-tracking design (an existing key's status is never
  overwritten by a re-fetch, only its live fields like score/salary
  are), not a separate mechanism. `declined` and `pass` are otherwise
  interchangeable; `declined` exists as the more natural word for "this
  specific application didn't work out" versus `pass`'s "not
  interested in the first place."

See `job-agent/README.md` for full details on each script.
