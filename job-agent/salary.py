#!/usr/bin/env python3
"""Extract disclosed salary ranges from a job board provider's payload.

Only reports a range when the posting structurally discloses one:
- Greenhouse: a pay-transparency metadata field (companies like Precision
  Medicine Group/Precision for Medicine) or a pay-transparency widget
  embedded in the job description HTML (companies like Iovance
  Biotherapeutics).
- Lever: the native `salaryRange` field, or failing that the free-text
  `salaryDescription` field the poster wrote specifically for pay
  disclosure (not the general job description).
Never guesses at a figure from free-text mentions elsewhere in the
description (e.g. budget/revenue numbers) — if no structured signal is
present, the job is reported as "Not disclosed", which is the norm for
non-US postings.
"""

import html
import re

NOT_DISCLOSED = "Not disclosed"

_PAY_RANGE_DIV_RE = re.compile(
    r'class="pay-range">\s*<span>([^<]+)</span>.*?<span>([^<]+)</span>', re.S
)


def extract_salary(job_detail):
    """Greenhouse job detail payload (from fetch_job_detail())."""
    for field in job_detail.get("metadata") or []:
        if field.get("value_type") == "currency_range" and field.get("value"):
            value = field["value"]
            unit = value.get("unit", "")
            lo, hi = value.get("min_value"), value.get("max_value")
            if lo and hi:
                return f"${int(float(lo)):,}–${int(float(hi)):,} {unit}".strip()

    content = html.unescape(job_detail.get("content") or "")
    match = _PAY_RANGE_DIV_RE.search(content)
    if match:
        return f"{match.group(1).strip()}–{match.group(2).strip()}"

    return NOT_DISCLOSED


def extract_salary_lever(posting):
    """Lever posting payload (from fetch_lever_jobs.fetch_jobs())."""
    salary_range = posting.get("salaryRange")
    if salary_range and salary_range.get("min") and salary_range.get("max"):
        lo, hi = int(salary_range["min"]), int(salary_range["max"])
        currency = salary_range.get("currency", "USD")
        return f"${lo:,}–${hi:,} {currency}"

    description = (posting.get("salaryDescriptionPlain") or "").strip()
    if description:
        return description

    return NOT_DISCLOSED
