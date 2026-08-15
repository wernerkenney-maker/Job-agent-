#!/usr/bin/env python3
"""Draft and save tailored resume bullet adjustments for high-scoring
matches (80+), alongside the cover letter.

save_resume_bullets() is used by both the live (match_jobs.py) and manual
scoring paths, so drafts land in the same place either way.
"""

import os

from cover_letter import slugify, strip_html

RESUME_BULLETS_DIR = os.path.join(os.path.dirname(__file__), "resume_bullets")

RESUME_BULLETS_PROMPT = """
Rewrite 3-4 resume bullets tailored to this specific job, pulling only
from the candidate's real background below. Do not invent
accomplishments, metrics, employers, or responsibilities that aren't in
the background provided. Emphasize whichever real experience maps most
directly onto what this role needs; reorder/reword, don't fabricate.
Each bullet: one line, action-verb led, quantified where the background
gives a real number.

Candidate background:
{profile}

Job title: {title}
Company: {company}
Job description:
{description}

Respond with ONLY the bullets, one per line, each starting with "- ".
No preamble, no header, no closing remarks.
"""


def resume_bullets_path(job):
    slug = slugify(job["title"], job["company"])
    return os.path.join("resume_bullets", f"{slug}.md")


def save_resume_bullets(job, bullets_text):
    os.makedirs(RESUME_BULLETS_DIR, exist_ok=True)
    rel_path = resume_bullets_path(job)
    abs_path = os.path.join(os.path.dirname(__file__), rel_path)
    header = f"# Resume bullet adjustments — {job['title']} ({job['company']})\n\n"
    with open(abs_path, "w") as f:
        f.write(header + bullets_text.strip() + "\n")
    return rel_path


def generate_resume_bullets_via_claude(client, job, description_html, candidate_profile, model):
    prompt = RESUME_BULLETS_PROMPT.format(
        profile=candidate_profile,
        title=job["title"],
        company=job["company"],
        description=strip_html(description_html)[:6000],
    )
    response = client.messages.create(
        model=model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
