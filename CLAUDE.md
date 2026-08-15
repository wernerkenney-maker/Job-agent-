# job-agent

Job search tooling for remote clinical operations / quality / regulatory
affairs / medical affairs / adjacent pharma-biotech leadership roles
(work-from-Brazil required). Code lives in `job-agent/`.

## "check jobs" shorthand

When the user says **"check jobs"**, treat it as the complete instruction
to do all of the following, without asking for confirmation:

1. Run today's check: fetch current listings from every company board in
   `job-agent/fetch_greenhouse_jobs.py`'s `COMPANIES` dict.
2. Score each job for fit against the candidate background in
   `job-agent/match_jobs.py`'s `CANDIDATE_PROFILE`, using the broadened
   rubric in `SCORING_INSTRUCTIONS`:
   - Not limited to an exact title match — clinical operations, quality,
     regulatory affairs, medical affairs, and other pharma/biotech
     leadership functions are all in scope where the candidate's
     experience is a strong transferable fit.
   - Prioritize compensation and long-term career trajectory over exact
     title wording. A junior/contract-type role (e.g. "Associate",
     "Consultant") should score lower than a permanent
     managerial/director-level role, even in a closer-sounding function.
   - Hard requirement, not traded off against anything above: the role
     must plausibly be performable remotely from Brazil (explicit Brazil
     location, or a LATAM-inclusive remote scope). Cap at 40 otherwise.
   - If `ANTHROPIC_API_KEY` is set, run `python3 match_jobs.py` directly —
     it fetches, scores via the Claude API (including this rubric),
     looks up salary for matches, and writes the report itself.
   - If no API key is available, score manually (as Claude, in
     conversation) using the same rubric, update
     `job-agent/manual_matches.json` with the fresh results — including a
     real `salary` value per job (see step 3, never invented) — then run
     `python3 apply_manual_scores.py` to regenerate the report.
3. Look up a salary range for each matched job via
   `job-agent/salary.py` (`extract_salary()`), fetching job detail with
   `fetch_greenhouse_jobs.fetch_job_detail()`. Only report a range when
   the posting structurally discloses one (Greenhouse pay-transparency
   metadata or an embedded pay-range widget) — never infer or guess a
   number from other figures in the description (e.g. budget/revenue
   mentions). If not structurally disclosed, report `"Not disclosed"`
   rather than a guess — this is expected and common for non-US postings.
4. Update `job-agent/report.html` with the fresh matches (score 60+,
   sorted highest first, each showing its salary) — this happens
   automatically via `report.write_report()` in both paths above.
5. `report.html` must keep every job title as its own clickable link
   straight to the posting (not just the surrounding card).
6. Summarize the results back to the user (what changed since last time,
   if anything — including any new matches surfaced purely by the
   broadened role rubric) and mention the updated report.

See `job-agent/README.md` for full details on each script.
