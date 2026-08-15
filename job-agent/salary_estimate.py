#!/usr/bin/env python3
"""Rough market-rate salary estimates for postings that don't disclose a
real range. Always clearly labeled as an estimate, never presented as
employer-disclosed data — see salary.py for the real, structural
extraction this falls back from.
"""

import json
import os


def format_estimate(low, high, note="", currency="USD"):
    label = f"~${low:,}–${high:,} {currency} (estimated"
    if note:
        label += f" — {note}"
    label += ", not disclosed by employer)"
    return label


ESTIMATE_PROMPT = """
This job posting does not disclose a salary. Give a rough, conservative
market-rate ANNUAL BASE salary range in USD, based on general industry
knowledge of this role's function, seniority, and location. This is only
a directional estimate, not sourced data, so keep the range wide enough
to be defensible.

Title: {title}
Company: {company}
Location: {location}
Context: {reason}

Respond with ONLY a JSON object, no other text:
{{"low": <integer USD>, "high": <integer USD>, "note": "<very short basis, under 12 words>"}}
"""


def estimate_salary_via_claude(client, job, model):
    prompt = ESTIMATE_PROMPT.format(
        title=job["title"],
        company=job["company"],
        location=job.get("location", ""),
        reason=job.get("reason", ""),
    )
    response = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    data = json.loads(text)
    return format_estimate(data["low"], data["high"], data.get("note", ""))
