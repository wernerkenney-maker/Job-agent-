#!/usr/bin/env python3
"""Merge sibling postings of the same role across a corporate family (e.g.
Precision Medicine Group / Precision for Medicine / Precision AQ) into a
single match with multiple apply links, instead of showing duplicates.
"""

import re

from companies import COMPANY_FAMILIES


def _family(company):
    return COMPANY_FAMILIES.get(company, company)


def _normalize_title(title):
    return re.sub(r"\s+", " ", title).strip().lower()


def match_key(company, title):
    """Canonical identity for a role, stable across sibling boards and runs."""
    return f"{_family(company)}::{_normalize_title(title)}"


def merge_sibling_postings(matches):
    """Group raw per-posting matches by (family, normalized title) and
    collapse each group into one match with a `postings` list."""
    groups = {}
    order = []
    for job in matches:
        key = match_key(job["company"], job["title"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(job)

    merged = []
    for key in order:
        jobs = groups[key]
        primary = max(jobs, key=lambda j: j["score"])
        postings = [
            {"company": j["company"], "url": j["url"], "location": j.get("location", "")}
            for j in jobs
        ]
        salary = next(
            (j["salary"] for j in jobs if j.get("salary") and j["salary"] != "Not disclosed"),
            jobs[0].get("salary", "Not disclosed"),
        )
        relocation = next((j.get("relocation") for j in jobs if j.get("relocation")), None)
        merged.append(
            {
                "key": key,
                "title": primary["title"],
                "company": primary["company"],
                "companies": sorted({j["company"] for j in jobs}),
                "postings": postings,
                "location": primary.get("location", ""),
                "score": primary["score"],
                "reason": primary["reason"],
                "salary": salary,
                "category": primary.get("category", "Adjacent"),
                "probability": primary.get("probability", "Medium"),
                "trajectory": primary.get("trajectory", ""),
                "relocation": relocation,
                "market": primary.get("market", "International (remote)"),
                "tier": primary.get("tier"),
            }
        )
    return merged
