# job-agent

Job search tooling for clinical operations / quality / regulatory affairs
/ medical affairs / adjacent pharma-biotech leadership roles workable
from Brazil — remote, or on-site/hybrid anywhere in the country.
Candidate is based in Fortaleza. Code lives in `job-agent/`.

## "check jobs" shorthand

When the user says **"check jobs"**, treat it as the complete instruction
to do all of the following, without asking for confirmation:

1. Fetch current listings from every company board across all six
   provider modules: `job-agent/fetch_greenhouse_jobs.py`,
   `job-agent/fetch_lever_jobs.py`, `job-agent/fetch_workable_jobs.py`,
   `job-agent/fetch_smartrecruiters_jobs.py`,
   `job-agent/fetch_ashby_jobs.py`, `job-agent/fetch_gupy_jobs.py` (each
   has its own `COMPANIES` dict; Ashby's is currently empty — see its
   module docstring/README for search notes before re-searching). The
   first five are **international employers** hiring remotely into
   Brazil (tag every job they produce `"market": "International
   (remote)"`); Gupy covers **genuinely Brazilian-market employers**
   hiring locally in BRL (tag its jobs `"market": "Brazilian market
   (local)"`) — see `job-agent/README.md`'s "International vs. Brazilian
   market" section for the search methodology and exclusions. Sibling-
   family mapping for dedup lives in `job-agent/companies.py`
   (`COMPANY_FAMILIES`), shared by all.
2. Score each job for fit against `CANDIDATE_PROFILE` in
   `job-agent/match_jobs.py`, using the broadened rubric in
   `SCORING_INSTRUCTIONS`: not limited to an exact title match (clinical
   operations, quality, regulatory affairs, medical affairs, and other
   pharma/biotech leadership functions are all in scope where experience
   is a strong transferable fit); prioritize compensation and long-term
   career trajectory over exact title wording (junior/contract-type
   roles score lower than permanent managerial/director-level roles);
   hard requirement, not traded off: the role must be workable from
   Brazil — either explicitly remote/LATAM-inclusive, or physically
   on-site/hybrid anywhere in Brazil (cap at 40 otherwise). Also assign,
   per job: `category` ("In-field" direct clinical-ops/trial-management
   work, or "Adjacent" transferable-skills fit elsewhere), `probability`
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
   level, a real step down in scope and pay from the candidate's
   Portfolio Manager role, and that trade-off belongs in the score and
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
3. The pipeline (`job-agent/pipeline.py`, used identically by both paths
   above) then:
   - **Dedupes sibling postings** (`job-agent/dedup.py`): the same role
     posted on multiple boards from the same corporate family (per
     `COMPANY_FAMILIES`, e.g. Precision Medicine Group / Precision for
     Medicine / Precision AQ) is shown once, with other boards' links
     noted.
   - **Tracks seen jobs** (`job-agent/jobs_state.py`,
     `job-agent/jobs_state.json`): only matches new since the last check
     are surfaced as "New matches" in the report. Anything the user has
     marked `interested` or `applied` (via `set_status.py`) stays visible
     in a "Tracked" section regardless of whether it's new this run.
     Anything marked `pass` is hidden from the report entirely. A match
     that scored 60+ before and was never actioned does not resurface —
     don't re-show the same jobs every day.
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
4. Update `job-agent/report.html` with the fresh matches (score 60+,
   "New matches" + "Tracked" sections, each showing a market tag
   ("International (remote)" / "Brazilian market (local)")
   category/probability tags, salary/estimate, cost-of-living note,
   relocation-support flag, a trajectory callout, sibling links, status,
   and cover letter/resume bullets links where applicable) — this happens
   automatically via `report.write_report()` in both paths above. Whenever
   a section contains both markets, it's split into two labeled
   subsections so international and Brazilian-market results can be
   compared side by side rather than interleaved by score. Note: draft
   links only render for jobs currently in one of those two sections — a
   job that already has drafts but has scrolled out of "new" (seen
   before, no status set) still has the files in the repo, just not
   linked from the report until it's marked `interested`/`applied`.
5. `report.html` must keep every job title as its own clickable link
   straight to the (primary) posting, and its header must show the pace
   tracker: a running "N applied this week · M all-time" count from
   `job-agent/applications_log.json` (`job-agent/pace_tracker.py`),
   logged automatically whenever `set_status.py <url> applied` is run.
6. Summarize the results back to the user (what's new since last time,
   any status changes reflected, any cover letters/resume bullets
   drafted) and mention the updated report.

See `job-agent/README.md` for full details on each script.
