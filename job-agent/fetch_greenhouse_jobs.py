#!/usr/bin/env python3
"""Fetch open job listings from a company's Greenhouse job board and print them.

Note: Thermo Fisher's careers site (jobs.thermofisher.com) is built on Phenom
People, not Greenhouse, so no boards-api.greenhouse.io/v1/boards/thermofisher
endpoint exists. This script is written against a real Greenhouse-hosted board
(Iovance Biotherapeutics, a clinical-stage biotech) as a working example; swap
BOARD_TOKEN for any other company's Greenhouse board token.
"""

import requests

BOARD_TOKEN = "iovancebiotherapeutics"
GREENHOUSE_URL = f"https://boards-api.greenhouse.io/v1/boards/{BOARD_TOKEN}/jobs"


def fetch_jobs():
    response = requests.get(GREENHOUSE_URL, timeout=30)
    response.raise_for_status()
    return response.json().get("jobs", [])


def main():
    jobs = fetch_jobs()
    print(f"Found {len(jobs)} open jobs at {BOARD_TOKEN}:\n")
    for job in jobs:
        print(job["title"])
        print(job["absolute_url"])
        print()


if __name__ == "__main__":
    main()
