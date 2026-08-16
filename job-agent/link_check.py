#!/usr/bin/env python3
"""Check whether a tracked posting URL is still live, for the daily scan's
expired-link check on *existing* tracked matches (separate from fetching
*new* listings).

Not every ATS returns a clean 404/410 for a pulled posting -- Greenhouse in
particular redirects a dead job URL to the board root with a 200 OK and an
`?error=true` query param (confirmed directly: job-boards.greenhouse.io/
precisionmedicinegroup/jobs/5793622004 returns HTTP 200, final URL
`.../precisionmedicinegroup?error=true`). A plain status-code check would
call that "live". So this checks, in order: the HTTP status, whether a
redirect landed on a known error-page URL pattern, and whether the page
body itself says the posting is gone -- across whichever of those signals
a given ATS actually uses.

Network failures (timeout, DNS, connection reset) return "unknown" rather
than "expired" -- a transient failure must never silently mark a real,
live posting as gone.
"""

import requests

_ERROR_URL_MARKERS = ("error=true", "/404", "not-found", "notfound", "job-not-found")

_ERROR_TEXT_MARKERS = (
    "job not found",
    "position has been filled",
    "no longer available",
    "no longer accepting applications",
    "posting has expired",
    "this position is closed",
    "requisition is no longer active",
    "página não encontrada",
    "vaga não encontrada",
    "vaga encerrada",
    "vaga expirada",
)


def check_link_status(url, timeout=15):
    """Returns "live", "expired", or "unknown" (network failure -- caller
    should leave the prior status untouched rather than treat this as a
    verdict)."""
    try:
        response = requests.get(
            url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True
        )
    except requests.RequestException:
        return "unknown"

    if response.status_code in (404, 410, 451):
        return "expired"
    if response.status_code >= 400:
        return "unknown"

    final_url = response.url or url
    if final_url != url and any(marker in final_url.lower() for marker in _ERROR_URL_MARKERS):
        return "expired"

    body = (response.text or "")[:20000].lower()
    if any(marker in body for marker in _ERROR_TEXT_MARKERS):
        return "expired"

    return "live"
