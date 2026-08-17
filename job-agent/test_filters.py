#!/usr/bin/env python3
"""Tests for the filters that decide what reaches scoring at all.

These guard the pipeline's silent-failure surfaces. A filter that wrongly
excludes a posting produces no error and no log line -- the job simply
never appears, which is indistinguishable from "nothing was posted." Two
such bugs have already shipped here:

  1. A title-keyword pre-filter dropped "Site Activation Manager" (IQVIA)
     and "Senior Site Navigator" (Fortrea) -- both genuinely Brazil-
     eligible, Manager-level roles whose titles carry no seniority word.
  2. Its replacement, a location filter matching only "brazil|brasil",
     dropped all 14 Syneos Health Brazil postings, because Syneos writes
     locations as ISO-3166 alpha-3 codes ("BRA-Remote") with no country
     name anywhere in the string.

Run: python3 test_filters.py
"""

import re
import sys
import types

# match_jobs imports the anthropic SDK at module scope for the API scoring
# path; stub it so these pure-function tests run without a key installed.
sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))

import match_jobs  # noqa: E402
from br_salary_estimate import estimate_br_salary  # noqa: E402
from dedup import match_key  # noqa: E402
from link_check import _ERROR_TEXT_MARKERS, _ERROR_URL_MARKERS  # noqa: E402


def _eligible(location, market="International (remote)"):
    return match_jobs._is_location_eligible({"location": location, "market": market})


# (location string, expected, which provider writes it this way)
LOCATION_CASES = [
    ("São Paulo, Brazil", True, "IQVIA"),
    ("Remote, Brazil", True, "Thermo Fisher"),
    ("Brazil-Remote", True, "Parexel"),
    ("Brazil-Sao Paulo", True, "Parexel"),
    ("Brazil, Sao Paulo", True, "ICON plc"),
    ("BRA-Remote", True, "Syneos Health (ISO alpha-3, no country name)"),
    ("BRA-Client", True, "Syneos Health"),
    ("ARG-Remote; CHL-Remote; MEX-Remote; BRA-Remote", True, "Syneos, multi-country"),
    ("São Paulo; Remote Brazil", True, "Fortrea, resolved multi-location"),
    ("Rio de Janeiro, Brazil", True, "Kyndryl"),
    ("Hortolandia, São Paulo, Brazil", True, "Kyndryl"),
    ("Remote, Argentina; Remote, Brazil; Remote, Mexico", True, "Greenhouse/Precision"),
    # Ambiguous -- must stay eligible so the description can resolve them.
    ("Remote", True, "bare remote, country unknown"),
    ("", True, "no location text at all"),
    # Genuinely ineligible: a specific non-Brazil geography.
    ("Beijing, China", False, "China only"),
    ("Remote, United States", False, "US only"),
    ("Warsaw", False, "Poland only"),
    ("GBR-Remote; HUN-Remote; POL-Remote", False, "EMEA only, ISO codes"),
    ("Mexico City, Mexico", False, "Mexico only"),
    ("USA-IL-Remote; USA-NE-Remote", False, "US states, ISO-style"),
]

GUPY_CASE = ("On-site, Campinas, SP", "Brazilian market (local)", True)

# Titles that a keyword-based seniority filter would wrongly reject, but
# whose descriptions show real Manager-level scope. These must never be
# excluded before scoring -- title is a label on the result, not a gate.
TITLES_THAT_MUST_NOT_BE_PRE_FILTERED = [
    "Site Activation Manager (Global)",
    "Senior Site Navigator",
    "Clinical Team Lead",
    "AD, Program Management CRGTO",
    "Coordenador de Pesquisa Clínica",
    "Gerente de Relacionamento Médico e Institucional",
]

BR_SALARY_CASES = [
    # (title, must_appear_in_note) -- guards against a title silently
    # falling through to the generic band with a misleading source label.
    ("Coordenador de Pesquisa Clínica", "Pesquisa Clínica"),
    ("Coordenador(a) Planejamento Estratégico", "Planejamento"),
    ("Gerente de Assistência Técnica e Serviços", "Gerente"),
]

DEDUP_CASES = [
    # Sibling boards of one corporate family must collapse to one key.
    (("Precision Medicine Group", "Clinical Trial Manager (LATAM)"),
     ("Precision for Medicine", "Clinical Trial Manager (LATAM)"), True),
    (("Precision AQ", "Director, FP&A"), ("Precision for Medicine", "Director, FP&A"), True),
    # Whitespace/case noise must not create a second entry.
    (("IQVIA", "Site Activation Manager  (Global)"),
     ("IQVIA", "site activation manager (global)"), True),
    # Genuinely different roles must stay separate.
    (("IQVIA", "Clinical Trial Manager"), ("Fortrea", "Clinical Trial Manager"), False),
]


def run():
    failures = []

    for location, expected, provider in LOCATION_CASES:
        got = _eligible(location)
        if got is not expected:
            failures.append(f"location {location!r} ({provider}): expected {expected}, got {got}")

    loc, market, expected = GUPY_CASE
    if _eligible(loc, market) is not expected:
        failures.append(f"Gupy market {loc!r}: expected {expected}")

    # A title must never on its own make a Brazil-located posting ineligible.
    for title in TITLES_THAT_MUST_NOT_BE_PRE_FILTERED:
        if not _eligible("São Paulo, Brazil"):
            failures.append(f"title-agnostic: {title!r} location wrongly excluded")

    for title, must_contain in BR_SALARY_CASES:
        note = estimate_br_salary(title)
        if must_contain.lower() not in note.lower():
            failures.append(f"br_salary {title!r}: note missing {must_contain!r} -> {note}")
        if "not disclosed by employer" not in note:
            failures.append(f"br_salary {title!r}: estimate not labeled as an estimate")

    for (c1, t1), (c2, t2), should_match in DEDUP_CASES:
        same = match_key(c1, t1) == match_key(c2, t2)
        if same is not should_match:
            failures.append(f"dedup {c1}/{t1!r} vs {c2}/{t2!r}: expected same={should_match}")

    # link_check must treat Greenhouse's 200-with-?error=true as expired.
    if not any("error=true" in m for m in _ERROR_URL_MARKERS):
        failures.append("link_check: lost the Greenhouse ?error=true redirect signal")
    if not any("no longer available" in m for m in _ERROR_TEXT_MARKERS):
        failures.append("link_check: lost the 'no longer available' body signal")

    total = (len(LOCATION_CASES) + 1 + len(TITLES_THAT_MUST_NOT_BE_PRE_FILTERED)
             + len(BR_SALARY_CASES) + len(DEDUP_CASES) + 2)
    if failures:
        print(f"FAILED {len(failures)} of {total} checks:\n")
        for f in failures:
            print("  -", f)
        return 1
    print(f"ok - {total} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
