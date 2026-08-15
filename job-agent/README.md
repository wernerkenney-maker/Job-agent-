# job-agent

Tools for finding remote clinical trials / clinical operations roles
(work-from-Brazil friendly).

## Current state

`fetch_greenhouse_jobs.py` fetches open listings from a company's public
Greenhouse job board API and prints each job's title and link.

Usage:

```
pip install -r requirements.txt
python3 fetch_greenhouse_jobs.py
```

**Note on Thermo Fisher:** Thermo Fisher's careers site
(jobs.thermofisher.com) runs on Phenom People, not Greenhouse, so there is
no `boards-api.greenhouse.io/v1/boards/thermofisher/jobs` endpoint. The
script currently points at Iovance Biotherapeutics
(`BOARD_TOKEN = "iovancebiotherapeutics"`), a real clinical-stage biotech
on Greenhouse, as a working example. Change `BOARD_TOKEN` in the script to
point at any other company's Greenhouse board.

Fetching Thermo Fisher's actual listings will need a separate script
against its real source (Phenom People) — planned as a next step.
