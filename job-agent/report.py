#!/usr/bin/env python3
"""Generate report.html from tracked job state.

Used by match_jobs.py after a live scoring run, and by
apply_manual_scores.py after a manual (conversation-based) scoring pass —
both go through pipeline.process_run() and then call write_report(), so
the output is always produced the same way.
"""

import html
import os
from datetime import datetime, timezone

from pace_tracker import total_count, weekly_count

SCORE_BANDS = (
    (85, "#1a7f5a", "#e6f6ef"),  # strong match
    (70, "#0f7ea8", "#e6f3f9"),  # good match
    (0, "#a86a10", "#fbf1de"),  # notable match
)

STATUS_LABELS = {
    "interested": ("Interested", "#0f7ea8", "#e6f3f9"),
    "applied": ("Applied", "#1a7f5a", "#e6f6ef"),
}

CATEGORY_COLORS = {
    "In-field": ("#1a7f5a", "#e6f6ef"),
    "Adjacent": ("#5c635d", "#eceeec"),
}

PROBABILITY_COLORS = {
    "High": ("#1a7f5a", "#e6f6ef"),
    "Medium": ("#a86a10", "#fbf1de"),
    "Long-shot": ("#a8341a", "#fbe9e6"),
}


def _band_colors(score):
    for threshold, fg, bg in SCORE_BANDS:
        if score >= threshold:
            return fg, bg
    return SCORE_BANDS[-1][1], SCORE_BANDS[-1][2]


def _salary_line(job):
    salary = job.get("salary") or "Not disclosed"
    if salary != "Not disclosed":
        return html.escape(salary), "salary"
    estimate = job.get("salary_estimate")
    if estimate:
        return html.escape(estimate), "salary estimate"
    return "Not disclosed", "salary undisclosed"


def _job_card(job):
    fg, bg = _band_colors(job["score"])
    title = html.escape(job["title"])
    location = html.escape(job.get("location", ""))
    reason = html.escape(job["reason"])
    postings = job["postings"]
    primary_url = html.escape(postings[0]["url"])
    salary_text, salary_class = _salary_line(job)
    location_html = f'<span class="loc">{location}</span>' if location else ""
    company_label = html.escape(" + ".join(job["companies"]))

    other_links = ""
    if len(postings) > 1:
        links = " &middot; ".join(
            f'<a href="{html.escape(p["url"])}" target="_blank" rel="noopener">{html.escape(p["company"])}</a>'
            for p in postings[1:]
        )
        other_links = f'<p class="also-posted">Also posted by: {links}</p>'

    status_html = ""
    if job["status"] in STATUS_LABELS:
        label, sfg, sbg = STATUS_LABELS[job["status"]]
        status_html = f'<span class="status" style="color:{sfg}; background:{sbg};">{label}</span>'

    draft_links = []
    if job.get("cover_letter_path"):
        path = html.escape(job["cover_letter_path"])
        draft_links.append(f'<a href="{path}">Cover letter draft &rarr;</a>')
    if job.get("resume_bullets_path"):
        path = html.escape(job["resume_bullets_path"])
        draft_links.append(f'<a href="{path}">Resume bullets &rarr;</a>')
    drafts_html = f'<div class="drafts">{"".join(f"<span>{link}</span>" for link in draft_links)}</div>' if draft_links else ""

    category = job.get("category", "Adjacent")
    cat_fg, cat_bg = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Adjacent"])
    probability = job.get("probability", "Medium")
    prob_fg, prob_bg = PROBABILITY_COLORS.get(probability, PROBABILITY_COLORS["Medium"])
    tags_html = (
        '<div class="tags">'
        f'<span class="tag" style="color:{cat_fg}; background:{cat_bg};">{html.escape(category)}</span>'
        f'<span class="tag" style="color:{prob_fg}; background:{prob_bg};">{html.escape(probability)}</span>'
        "</div>"
    )
    trajectory = job.get("trajectory", "")
    trajectory_html = f'<p class="trajectory">{html.escape(trajectory)}</p>' if trajectory else ""

    col_html = ""
    if job.get("col_note"):
        col_html = f'<p class="col-note">{html.escape(job["col_note"])}</p>'

    relocation_html = ""
    if job.get("relocation"):
        relocation_html = f'<p class="relocation">&#9992; {html.escape(job["relocation"])}</p>'

    return f"""
    <li class="card">
      <div class="card-top">
        <span class="score" style="color:{fg}; background:{bg};">{job["score"]}</span>
        <div class="titles">
          <a class="title" href="{primary_url}" target="_blank" rel="noopener">{title}</a>
          <span class="company">{company_label}{" · " + location_html if location else ""}</span>
        </div>
        {status_html}
      </div>
      {tags_html}
      <p class="reason">{reason}</p>
      <p class="{salary_class}">{salary_text}</p>
      {col_html}
      {relocation_html}
      {trajectory_html}
      {other_links}
      {drafts_html}
    </li>"""


def _section(title_text, matches, empty_text):
    if not matches:
        return f"""
    <section>
      <h2>{title_text}</h2>
      <p class="empty">{empty_text}</p>
    </section>"""
    cards = "\n".join(_job_card(job) for job in matches)
    return f"""
    <section>
      <h2>{title_text}</h2>
      <ul>
        {cards}
      </ul>
    </section>"""


def generate_report_html(new_matches, tracked_matches, scored_count, fetched_count, generated_at=None):
    generated_at = generated_at or datetime.now(timezone.utc)
    timestamp = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    pace_weekly = weekly_count(generated_at)
    pace_total = total_count()

    new_section = _section(
        "New matches",
        new_matches,
        "No new matches since your last check — same postings as before, nothing new to show.",
    )
    tracked_section = ""
    if tracked_matches:
        tracked_section = _section("Tracked (interested / applied)", tracked_matches, "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Clinical Ops Job Matches</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg: #f6f7f5;
    --surface: #ffffff;
    --border: #e3e5e0;
    --text: #1f2420;
    --text-muted: #5c635d;
    --accent: #2f6f4f;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #14171a;
      --surface: #1d2124;
      --border: #2c3134;
      --text: #eceeec;
      --text-muted: #a3aaa5;
      --accent: #6fbf95;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{
    max-width: 640px;
    margin: 0 auto;
    padding: 28px 18px 60px;
  }}
  header {{
    margin-bottom: 22px;
  }}
  h1 {{
    font-size: 1.5rem;
    margin: 0 0 6px;
    letter-spacing: -0.01em;
  }}
  h2 {{
    font-size: 1.05rem;
    margin: 0 0 12px;
  }}
  section + section {{
    margin-top: 30px;
  }}
  .subtitle {{
    color: var(--text-muted);
    font-size: 0.92rem;
    margin: 0 0 14px;
    line-height: 1.5;
  }}
  .pace {{
    display: inline-block;
    font-size: 0.85rem;
    color: var(--text);
    background: color-mix(in srgb, var(--accent) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
    border-radius: 999px;
    padding: 6px 14px;
    margin-bottom: 12px;
  }}
  .pace-figure {{
    font-weight: 700;
    color: var(--accent);
  }}
  .stats {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 0.82rem;
    color: var(--text-muted);
  }}
  .stats span {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 4px 12px;
  }}
  ul {{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
  }}
  .card-top {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }}
  .score {{
    flex: 0 0 auto;
    font-weight: 700;
    font-size: 0.95rem;
    border-radius: 10px;
    padding: 5px 9px;
    min-width: 2.4em;
    text-align: center;
  }}
  .titles {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    flex: 1 1 auto;
  }}
  .title {{
    font-weight: 600;
    font-size: 1rem;
    line-height: 1.3;
    color: var(--accent);
    text-decoration: underline;
    text-decoration-color: color-mix(in srgb, var(--accent) 40%, transparent);
    text-underline-offset: 2px;
  }}
  .title:hover, .title:focus {{
    text-decoration-color: var(--accent);
  }}
  .company {{
    font-size: 0.85rem;
    color: var(--text-muted);
  }}
  .loc {{
    color: var(--text-muted);
  }}
  .status {{
    flex: 0 0 auto;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 999px;
    padding: 4px 10px;
    white-space: nowrap;
  }}
  .tags {{
    display: flex;
    gap: 6px;
    margin: 10px 0 0;
    flex-wrap: wrap;
  }}
  .tag {{
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 999px;
    padding: 3px 9px;
  }}
  .reason {{
    margin: 10px 0 0;
    font-size: 0.9rem;
    color: var(--text-muted);
    line-height: 1.45;
  }}
  .trajectory {{
    margin: 8px 0 0;
    font-size: 0.85rem;
    color: var(--text);
    line-height: 1.4;
    padding-left: 10px;
    border-left: 2px solid var(--border);
  }}
  .salary {{
    margin: 8px 0 0;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text);
  }}
  .salary.estimate {{
    font-weight: 400;
    font-style: italic;
    color: var(--text-muted);
  }}
  .salary.undisclosed {{
    font-weight: 400;
    font-style: italic;
    color: var(--text-muted);
  }}
  .col-note {{
    margin: 6px 0 0;
    font-size: 0.78rem;
    font-style: italic;
    color: var(--text-muted);
    line-height: 1.4;
  }}
  .relocation {{
    margin: 8px 0 0;
    font-size: 0.82rem;
    color: var(--text);
  }}
  .also-posted {{
    margin: 8px 0 0;
    font-size: 0.78rem;
    color: var(--text-muted);
  }}
  .also-posted a {{
    color: var(--text-muted);
  }}
  .drafts {{
    margin: 10px 0 0;
    font-size: 0.85rem;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .drafts a {{
    color: var(--accent);
    font-weight: 600;
    text-decoration: none;
  }}
  .empty {{
    text-align: center;
    color: var(--text-muted);
    padding: 24px 0;
    font-size: 0.88rem;
  }}
  footer {{
    margin-top: 28px;
    font-size: 0.78rem;
    color: var(--text-muted);
    text-align: center;
    line-height: 1.6;
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Clinical Ops Job Matches</h1>
      <p class="subtitle">Clinical operations, quality, regulatory affairs, medical affairs, and adjacent pharma/biotech leadership roles, scored for fit, compensation, and career trajectory against your background — workable from Brazil required (remote, or on-site/hybrid anywhere in Brazil). Filtered to score 60+, sorted highest first. Sibling postings from the same corporate family are shown once.</p>
      <div class="pace">
        <span class="pace-figure">{pace_weekly}</span> applied this week &middot; <span class="pace-figure">{pace_total}</span> all-time
      </div>
      <div class="stats">
        <span>{len(new_matches)} new</span>
        <span>{len(tracked_matches)} tracked</span>
        <span>{scored_count} scored</span>
        <span>{fetched_count} fetched</span>
        <span>updated {timestamp}</span>
      </div>
    </header>
    {new_section}
    {tracked_section}
    <footer>
      Generated by match_jobs.py / manual scoring &middot; job-agent<br>
      Mark a job's status with: python3 set_status.py &lt;url&gt; applied|interested|pass
    </footer>
  </div>
</body>
</html>
"""


def write_report(new_matches, tracked_matches, scored_count, fetched_count, output_path=None, generated_at=None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "report.html")
    html_content = generate_report_html(new_matches, tracked_matches, scored_count, fetched_count, generated_at)
    with open(output_path, "w") as f:
        f.write(html_content)
    return output_path
