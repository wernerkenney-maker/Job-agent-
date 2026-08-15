# job-agent

Job search tooling for remote clinical trials / clinical operations roles
(work-from-Brazil friendly). Code lives in `job-agent/`.

## "check jobs" shorthand

When the user says **"check jobs"**, treat it as the complete instruction
to do all of the following, without asking for confirmation:

1. Run today's check: fetch current listings from every company board in
   `job-agent/fetch_greenhouse_jobs.py`'s `COMPANIES` dict.
2. Score each job for fit against the candidate background in
   `job-agent/match_jobs.py`'s `CANDIDATE_PROFILE`.
   - If `ANTHROPIC_API_KEY` is set, run `python3 match_jobs.py` directly —
     it fetches, scores via the Claude API, and writes the report itself.
   - If no API key is available, score manually (as Claude, in
     conversation) using the same rubric, update
     `job-agent/manual_matches.json` with the fresh results, then run
     `python3 apply_manual_scores.py` to regenerate the report.
3. Update `job-agent/report.html` with the fresh matches (score 60+,
   sorted highest first) — this happens automatically via
   `report.write_report()` in both paths above.
4. Report.html must keep every job title as a clickable link straight to
   the posting (not just the surrounding card).
5. Summarize the results back to the user (what changed since last time,
   if anything) and mention the updated report.

See `job-agent/README.md` for full details on each script.
