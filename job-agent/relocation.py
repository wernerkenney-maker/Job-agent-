#!/usr/bin/env python3
"""Detect explicit relocation-support signals in a job description:
relocation assistance, a home-office/equipment stipend, or a sign-on
bonus. Purely a text match against the posting's own wording — never
infers support from company size, role seniority, or anything else. If
none of these phrases appear, returns None (leave blank), not a guess.
"""

import html
import re

_PATTERNS = [
    (re.compile(r"relocation\s*(assistance|package|support|bonus|stipend)", re.I), "Relocation assistance"),
    (re.compile(r"sign(?:ing|-on)[\s-]*bonus", re.I), "Sign-on bonus"),
    (re.compile(r"home[\s-]?office\s*(stipend|allowance|equipment)", re.I), "Home-office/equipment stipend"),
    (re.compile(r"equipment\s*(stipend|allowance)", re.I), "Equipment stipend"),
    (re.compile(r"work[\s-]from[\s-]home\s*stipend", re.I), "Home-office stipend"),
    (re.compile(r"remote\s*work\s*stipend", re.I), "Remote-work stipend"),
]


def _strip_html(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^<]+?>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_relocation_support(description_html_or_text):
    text = _strip_html(description_html_or_text)
    found = []
    for pattern, label in _PATTERNS:
        if pattern.search(text) and label not in found:
            found.append(label)
    return ", ".join(found) if found else None
