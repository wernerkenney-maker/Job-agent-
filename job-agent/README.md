# job-agent

Tools for finding remote clinical trials / clinical operations roles
(work-from-Brazil friendly).

## Current state

`fetch_greenhouse_jobs.py` fetches open listings from several companies'
public Greenhouse job board APIs and prints each job's title and link,
grouped by company.

Usage:

```
pip install -r requirements.txt
python3 fetch_greenhouse_jobs.py
```

Companies checked (`COMPANIES` dict in the script — add/remove
Greenhouse board tokens there):

- **Iovance Biotherapeutics** — clinical-stage biotech (cell therapy)
- **Precision Medicine Group** — CRO, has roles explicitly open to
  Remote/Brazil, Remote/LATAM
- **Precision for Medicine** — CRO business unit of Precision Medicine
  Group, also has Brazil/LATAM-remote clinical roles (Clinical Trial
  Manager (LATAM), Investigator Grants Associate (Brazil), etc.)
- **ClinChoice** — global CRO with a Brazil-based listing

**Note on Thermo Fisher:** Thermo Fisher's careers site
(jobs.thermofisher.com) runs on Phenom People, not Greenhouse, so there is
no `boards-api.greenhouse.io/v1/boards/thermofisher/jobs` endpoint. Fetching
Thermo Fisher's actual listings will need a separate script against its
real source (Phenom People) — planned as a next step.

Other Greenhouse tokens tried and confirmed *not* to exist for major
CROs/biotechs (in case useful later): `medable`, `curebase`, `advarra`,
`icon` (returns an empty "ICON Talent Community" board, not ICON plc),
`fortrea`, `veevasystems`, `certara`.

## Resume-based matching

`match_jobs.py` fetches jobs from all companies in `COMPANIES` (reusing
`fetch_greenhouse_jobs.py`), sends them to Claude in batches to score fit
(1-100) against a candidate background hardcoded in `CANDIDATE_PROFILE`,
then prints only jobs scoring 60+ (`MIN_SCORE`), sorted highest first,
each with a one-line reason.

Requires an Anthropic API key:

```
export ANTHROPIC_API_KEY=sk-ant-...
pip install -r requirements.txt
python3 match_jobs.py
```

Edit `CANDIDATE_PROFILE` at the top of `match_jobs.py` to update the
background used for scoring. `CLAUDE_MODEL` env var overrides the model
(defaults to `claude-sonnet-5`).
