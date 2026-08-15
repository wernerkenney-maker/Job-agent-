#!/usr/bin/env python3
"""Extract disclosed salary ranges from a Greenhouse job detail payload.

Only reports a range when the posting structurally discloses one — either
via a Greenhouse pay-transparency metadata field (used by companies like
Precision Medicine Group/Precision for Medicine) or a pay-transparency
widget embedded in the job description HTML (used by companies like
Iovance Biotherapeutics). Never guesses at a figure from free-text
mentions elsewhere in the description (e.g. budget/revenue numbers) —
if neither structured signal is present, the job is reported as
"Not disclosed", which is the norm for non-US postings.
"""

import html
import re

NOT_DISCLOSED = "Not disclosed"

_PAY_RANGE_DIV_RE = re.compile(
    r'class="pay-range">\s*<span>([^<]+)</span>.*?<span>([^<]+)</span>', re.S
)


def extract_salary(job_detail):
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
