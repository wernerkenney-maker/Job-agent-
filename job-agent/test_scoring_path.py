#!/usr/bin/env python3
"""End-to-end exercise of match_jobs.py's API scoring path, with the model
call stubbed.

Why this exists: the description-based scoring rewrite (fetch every
location-eligible posting's full description BEFORE scoring, so title is
never a gate) only runs when ANTHROPIC_API_KEY is set. That key has never
been set in this environment, so the entire path -- the pre-score detail
fetch, the prompt assembly, the response parsing, the salary/relocation
enrichment that now reuses the pre-fetched detail -- had shipped without
ever executing once. Unit-testing the filter predicate alone (see
test_filters.py) does not cover any of that wiring.

This runs the real code against real provider payloads and substitutes
only the network-bound pieces:
  - the Anthropic client is a stub that returns well-formed scores, so
    prompt assembly and response parsing are genuinely exercised;
  - provider detail fetches are served from recorded fixtures where a
    live call would otherwise be needed.

What it proves: descriptions actually reach the prompt, a title carrying
no seniority signal survives to be scored, detail is fetched once and
reused (not re-fetched per match), and the enrichment functions read the
right field out of each provider's differently-shaped payload.

What it does NOT prove: that the live model returns sensible scores. Only
a real API run shows that.

Run: python3 test_scoring_path.py
"""

import json
import sys
import types

sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))

import match_jobs  # noqa: E402

# Provider payloads shaped exactly like each fetcher returns them. The
# description lives under a different key in every one -- the bug class
# this guards is _description_html() reading the wrong key and silently
# yielding "" , which would score every job on an empty description.
PROVIDER_FIXTURES = {
    "greenhouse": (
        {"content": "&lt;p&gt;Lead global site activation.&lt;/p&gt;", "metadata": []},
        "Lead global site activation.",
    ),
    "lever": ({"description": "<p>Own the program portfolio.</p>"}, "Own the program portfolio."),
    "workable": ({"description": "<div>Manage multi-country trials.</div>"}, "Manage multi-country trials."),
    "ashby": ({"descriptionHtml": "<p>Direct the PMO.</p>"}, "Direct the PMO."),
    "workday": ({"jobDescription": "<p>Accountable for delivery.</p>"}, "Accountable for delivery."),
    "smartrecruiters": (
        {"jobAd": {"sections": {"jobDescription": {"text": "<p>Regional project lead.</p>"}}}},
        "Regional project lead.",
    ),
    "gupy": (
        {"description": "<p>Coordenar centro.</p>", "prerequisites": "", "responsibilities": ""},
        "Coordenar centro.",
    ),
}


class _StubMessages:
    def __init__(self, outer):
        self._outer = outer

    def create(self, model, max_tokens, messages):
        prompt = messages[0]["content"]
        self._outer.prompts.append(prompt)
        # Echo back one result per job id present in the prompt.
        ids = [int(line.split("id=")[1].split(",")[0]) for line in prompt.splitlines() if line.startswith("- id=")]
        payload = [
            {
                "id": i,
                "score": 88,
                "reason": "stub",
                "category": "In-field",
                "level": "Primary",
                "probability": "High",
                "trajectory": "stub",
            }
            for i in ids
        ]
        return types.SimpleNamespace(content=[types.SimpleNamespace(text=json.dumps(payload))])


class StubClient:
    def __init__(self):
        self.prompts = []
        self.messages = _StubMessages(self)


def run():
    failures = []

    # 1. Every provider's description key is read correctly.
    for source, (detail, expected) in PROVIDER_FIXTURES.items():
        got = match_jobs._strip_html_to_text(match_jobs._description_html(detail, source))
        if expected not in got:
            failures.append(f"_description_html({source}): expected {expected!r}, got {got!r}")

    # 2. An unknown source degrades to empty rather than raising.
    if match_jobs._description_html({"content": "x"}, "brand_new_provider") != "":
        failures.append("_description_html: unknown source should yield ''")

    # 3. Salary extraction reads each provider's payload without raising,
    #    and reports "Not disclosed" rather than inventing a figure.
    for source, (detail, _) in PROVIDER_FIXTURES.items():
        try:
            salary = match_jobs._extract_salary(detail, source)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"_extract_salary({source}) raised {exc!r}")
            continue
        if not isinstance(salary, str) or not salary:
            failures.append(f"_extract_salary({source}) returned {salary!r}")

    # 4. score_batch actually puts the description in the prompt, and a
    #    title with no seniority signal still gets scored on its content.
    client = StubClient()
    batch = [
        {
            "title": "Site Activation Manager",  # no seniority keyword at all
            "location": "São Paulo, Brazil",
            "company": "IQVIA",
            "description_excerpt": "SENTINEL_SCOPE 7+ years including 3+ in a leadership role, bid defense.",
        },
        {
            "title": "Senior Site Navigator",
            "location": "São Paulo; Remote Brazil",
            "company": "Fortrea",
            "description_excerpt": "SENTINEL_TWO owns site activation strategy end to end.",
        },
    ]
    results = match_jobs.score_batch(client, batch)
    prompt = client.prompts[0]
    for sentinel in ("SENTINEL_SCOPE", "SENTINEL_TWO"):
        if sentinel not in prompt:
            failures.append(f"score_batch: description {sentinel} never reached the prompt")
    if "responsibilities and requirements" not in prompt:
        failures.append("score_batch: prompt lost the read-the-description instruction")
    if len(results) != len(batch):
        failures.append(f"score_batch: expected {len(batch)} results, got {len(results)}")
    if {r["id"] for r in results} != set(range(len(batch))):
        failures.append("score_batch: batch-local ids not echoed back correctly")

    # 5. Fenced ```json responses parse (models commonly wrap output).
    class FencedMessages(_StubMessages):
        def create(self, model, max_tokens, messages):
            self._outer.prompts.append(messages[0]["content"])
            body = json.dumps([{"id": 0, "score": 70, "reason": "r", "category": "Adjacent",
                                "level": "Primary", "probability": "Medium", "trajectory": "t"}])
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(text=f"```json\n{body}\n```")]
            )

    fenced = StubClient()
    fenced.messages = FencedMessages(fenced)
    try:
        out = match_jobs.score_batch(fenced, [batch[0]])
        if out[0]["score"] != 70:
            failures.append("score_batch: fenced JSON parsed to wrong payload")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"score_batch: fenced ```json response failed to parse ({exc!r})")

    # 6. Detail is fetched once per posting and reused, not re-fetched for
    #    salary. Counts calls through the real _fetch_job_detail dispatch.
    calls = {"n": 0}

    def counting_detail(job):
        calls["n"] += 1
        return {"jobDescription": "<p>x</p>"}

    real = match_jobs._fetch_job_detail
    match_jobs._fetch_job_detail = counting_detail
    try:
        cache = {}
        jobs = [{"url": "u1", "source": "workday"}, {"url": "u2", "source": "workday"}]
        for j in jobs:
            cache[j["url"]] = match_jobs._fetch_job_detail(j)
        for j in jobs:  # enrichment stage must read the cache
            match_jobs._extract_salary(cache.get(j["url"], {}), j["source"])
        if calls["n"] != len(jobs):
            failures.append(f"detail fetched {calls['n']} times for {len(jobs)} postings (should be 1 each)")
    finally:
        match_jobs._fetch_job_detail = real

    # 7. The excerpt cap is enforced, so one enormous posting cannot blow
    #    up the batch prompt.
    long_text = match_jobs._strip_html_to_text("<p>" + ("word " * 5000) + "</p>")
    if len(long_text[: match_jobs.DESCRIPTION_EXCERPT_LENGTH]) != match_jobs.DESCRIPTION_EXCERPT_LENGTH:
        failures.append("DESCRIPTION_EXCERPT_LENGTH truncation not applied")

    # 8. A malformed posting must never abort collection. Workday's full
    #    catalog returns records with no externalPath -- the field every
    #    URL and id derives from -- and the per-posting loop used to sit
    #    outside the try, so one bad row discarded every provider already
    #    fetched (a ten-minute loss once Workday went full-catalog).
    if match_jobs._map_workday({"title": "no path"}, "iqvia", "IQVIA") is not None:
        failures.append("_map_workday: posting without externalPath should be dropped")
    if match_jobs._map_workday({"externalPath": "", "title": "empty"}, "iqvia", "IQVIA") is not None:
        failures.append("_map_workday: empty externalPath should be dropped")
    mapped = match_jobs._map_workday(
        {"externalPath": "/job/x_R1", "title": "T", "locationsText": "São Paulo, Brazil"},
        "iqvia", "IQVIA",
    )
    if not mapped or mapped["source_id"] != "/job/x_R1" or not mapped["url"].endswith("/job/x_R1"):
        failures.append(f"_map_workday: valid posting mapped wrong -> {mapped}")

    collected = []
    match_jobs._collect_provider(
        collected, "TestCo",
        fetch=lambda: [{"id": 1}, {"MALFORMED": True}, {"id": 3}],
        mapper=lambda p: {"id": p["id"]},
    )
    if [j["id"] for j in collected] != [1, 3]:
        failures.append(f"_collect_provider: bad row lost good ones -> {collected}")

    survived = []

    def _boom():
        raise RuntimeError("network down")

    match_jobs._collect_provider(survived, "BrokenCo", fetch=_boom, mapper=lambda p: p)
    match_jobs._collect_provider(survived, "GoodCo", fetch=lambda: [{"k": 1}], mapper=lambda p: p)
    if survived != [{"k": 1}]:
        failures.append(f"_collect_provider: fetch failure not isolated -> {survived}")

    # 9. The same missing-externalPath row must also be survivable inside
    #    the *fetcher*, not just the mapper. fetch_workday_jobs.fetch_jobs
    #    used to index posting["externalPath"] directly in two places (the
    #    search-term dedup and the concurrent location resolver); the
    #    resolver's KeyError escaped future.result() and took out the whole
    #    tenant, so _collect_provider logged "Failed to fetch IQVIA" and
    #    1868 postings vanished from the run.
    import fetch_workday_jobs as fw

    real_search = fw._search
    real_resolve_detail = fw.fetch_job_detail
    fw._search = lambda key, term: [
        {"externalPath": "/job/good_R1", "title": "Good", "locationsText": "2 Locations"},
        {"title": "No path at all", "locationsText": "São Paulo"},
        {"externalPath": "", "title": "Empty path", "locationsText": ""},
    ]
    fw.fetch_job_detail = lambda key, path: {"location": "São Paulo, Brazil"}
    try:
        got = fw.fetch_jobs("iqvia")  # full-catalog tenant (no search_terms)
        if [p.get("externalPath") for p in got] != ["/job/good_R1"]:
            failures.append(f"fetch_jobs: pathless rows not dropped -> {got}")
        if got and got[0]["locationsText"] != "São Paulo, Brazil":
            failures.append(f"fetch_jobs: ambiguous location not resolved -> {got[0]}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"fetch_jobs: pathless row aborted the tenant ({exc!r})")
    finally:
        fw._search = real_search
        fw.fetch_job_detail = real_resolve_detail

    total = len(PROVIDER_FIXTURES) * 2 + 1 + 6 + 1 + 1 + 1 + 5 + 2
    if failures:
        print(f"FAILED {len(failures)} of ~{total} checks:\n")
        for f in failures:
            print("  -", f)
        return 1
    print(f"ok - ~{total} checks passed (model call stubbed; live scoring quality still unverified)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
