#!/usr/bin/env python3
"""Generate report.html from a list of scored job matches.

Used by match_jobs.py after a live scoring run, and by
apply_manual_scores.py after a manual (conversation-based) scoring pass —
both call write_report() so the output is always produced the same way.
"""

import html
from datetime import datetime, timezone

SCORE_BANDS = (
    (85, "#1a7f5a", "#e6f6ef"),  # strong match
    (70, "#0f7ea8", "#e6f3f9"),  # good match
    (0, "#a86a10", "#fbf1de"),  # notable match
)


def _band_colors(score):
    for threshold, fg, bg in SCORE_BANDS:
        if score >= threshold:
            return fg, bg
    return SCORE_BANDS[-1][1], SCORE_BANDS[-1][2]


def _job_card(job):
    fg, bg = _band_colors(job["score"])
    title = html.escape(job["title"])
    company = html.escape(job["company"])
    location = html.escape(job.get("location", ""))
    reason = html.escape(job["reason"])
    url = html.escape(job["url"])
    location_html = f'<span class="loc">{location}</span>' if location else ""

    return f"""
    <li class="card">
      <div class="card-top">
        <span class="score" style="color:{fg}; background:{bg};">{job["score"]}</span>
        <div class="titles">
          <a class="title" href="{url}" target="_blank" rel="noopener">{title}</a>
          <span class="company">{company}{" · " + location_html if location else ""}</span>
        </div>
      </div>
      <p class="reason">{reason}</p>
    </li>"""


def generate_report_html(matches, scored_count, fetched_count, generated_at=None):
    generated_at = generated_at or datetime.now(timezone.utc)
    timestamp = generated_at.strftime("%Y-%m-%d %H:%M UTC")

    cards = "\n".join(_job_card(job) for job in matches) or (
        '<li class="empty">No jobs scored 60+ this run.</li>'
    )

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
  .subtitle {{
    color: var(--text-muted);
    font-size: 0.92rem;
    margin: 0 0 14px;
    line-height: 1.5;
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
  .reason {{
    margin: 10px 0 0;
    font-size: 0.9rem;
    color: var(--text-muted);
    line-height: 1.45;
  }}
  .empty {{
    text-align: center;
    color: var(--text-muted);
    padding: 40px 0;
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
      <p class="subtitle">Remote clinical trials / clinical operations roles scored for fit against your background, filtered to score 60+ and sorted highest first.</p>
      <div class="stats">
        <span>{len(matches)} matches</span>
        <span>{scored_count} scored</span>
        <span>{fetched_count} fetched</span>
        <span>updated {timestamp}</span>
      </div>
    </header>
    <ul>
      {cards}
    </ul>
    <footer>
      Generated by match_jobs.py / manual scoring &middot; job-agent
    </footer>
  </div>
</body>
</html>
"""


def write_report(matches, scored_count, fetched_count, output_path="report.html", generated_at=None):
    html_content = generate_report_html(matches, scored_count, fetched_count, generated_at)
    with open(output_path, "w") as f:
        f.write(html_content)
    return output_path
