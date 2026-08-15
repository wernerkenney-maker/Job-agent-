#!/usr/bin/env python3
"""Draft and save tailored cover letters for high-scoring matches (80+).

save_cover_letter() is used by both the live (match_jobs.py) and manual
scoring paths, so drafts land in the same place either way.
"""

import html
import os
import re

COVER_LETTER_DIR = os.path.join(os.path.dirname(__file__), "cover_letters")
COVER_LETTER_SCORE_THRESHOLD = 80

COVER_LETTER_PROMPT = """
Draft a short, tailored cover letter (250-350 words) from the candidate
below, applying to the job below. Professional but not stiff. Reference
1-2 concrete pieces of the candidate's background that map directly onto
what the role needs. Do not invent details not in the candidate
background or job description. End with a simple closing line, no
placeholder brackets like [Your Name].

Candidate background:
{profile}

Job title: {title}
Company: {company}
Location: {location}
Job description:
{description}
"""


def slugify(title, company):
    text = f"{company}-{title}".lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def cover_letter_path(job):
    slug = slugify(job["title"], job["company"])
    return os.path.join("cover_letters", f"{slug}.md")


def save_cover_letter(job, letter_text):
    os.makedirs(COVER_LETTER_DIR, exist_ok=True)
    rel_path = cover_letter_path(job)
    abs_path = os.path.join(os.path.dirname(__file__), rel_path)
    header = f"# Cover letter — {job['title']} ({job['company']})\n\n"
    with open(abs_path, "w") as f:
        f.write(header + letter_text.strip() + "\n")
    return rel_path


def strip_html(content):
    text = html.unescape(content or "")
    text = re.sub(r"<[^<]+?>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def generate_cover_letter_via_claude(client, job, description_html, candidate_profile, model):
    prompt = COVER_LETTER_PROMPT.format(
        profile=candidate_profile,
        title=job["title"],
        company=job["company"],
        location=job.get("location", ""),
        description=strip_html(description_html)[:6000],
    )
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
