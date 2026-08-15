# job-agent

Job search tooling for remote clinical operations / quality / regulatory
affairs / medical affairs / adjacent pharma-biotech leadership roles
(work-from-Brazil required). Code lives in `job-agent/`.

## "check jobs" shorthand

When the user says **"check jobs"**, treat it as the complete instruction
to do all of the following, without asking for confirmation:

1. Fetch current listings from every company board in
   `job-agent/fetch_greenhouse_jobs.py`'s `COMPANIES` dict.
2. Score each job for fit against `CANDIDATE_PROFILE` in
   `job-agent/match_jobs.py`, using the broadened rubric in
   `SCORING_INSTRUCTIONS`: not limited to an exact title match (clinical
   operations, quality, regulatory affairs, medical affairs, and other
   pharma/biotech leadership functions are all in scope where experience
   is a strong transferable fit); prioritize compensation and long-term
   career trajectory over exact title wording (junior/contract-type
   roles score lower than permanent managerial/director-level roles);
   hard requirement, not traded off: the role must plausibly be
   performable remotely from Brazil (cap at 40 otherwise).
   - If `ANTHROPIC_API_KEY` is set, run `python3 match_jobs.py` — it
     fetches, scores, and runs the full pipeline (below) itself.
   - If no API key is available, score manually (as Claude, in
     conversation) using the same rubric, record raw per-posting matches
     in `job-agent/manual_matches.json` (with a real, API-verified
     `salary` per posting — see step 4, never invented), record any
     cover letter text / salary estimate figures for this run in
     `job-agent/manual_extras.json`, then run
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
   - **Drafts cover letters** for any match scoring 80+ that doesn't have
     one yet (`job-agent/cover_letter.py`), saved to
     `job-agent/cover_letters/<slug>.md` for the user to review/edit —
     never auto-submitted anywhere.
   - **Estimates salary** when a posting doesn't disclose one
     (`job-agent/salary_estimate.py`): a rough, clearly-labeled
     market-rate range (e.g. "~$60,000–$90,000 USD (estimated — ...,
     not disclosed by employer)"), distinct from a real disclosed figure
     from `job-agent/salary.py` (which only ever reports a number when
     the posting structurally discloses one — metadata field or embedded
     pay-transparency widget — never inferred from other figures in the
     description).
4. Update `job-agent/report.html` with the fresh matches (score 60+,
   "New matches" + "Tracked" sections, each showing salary/estimate,
   sibling links, status, and cover letter link where applicable) — this
   happens automatically via `report.write_report()` in both paths above.
5. `report.html` must keep every job title as its own clickable link
   straight to the (primary) posting.
6. Summarize the results back to the user (what's new since last time,
   any status changes reflected, any cover letters drafted) and mention
   the updated report.

See `job-agent/README.md` for full details on each script.
