#!/usr/bin/env python3
"""Rough cost-of-living comparison against Fortaleza (the candidate's home
base) for Brazilian cities mentioned in a posting's location.

FORTALEZA_COL_INDEX is a rough, directional index (Fortaleza = 1.00),
based on general knowledge of regional cost-of-living variance in Brazil
(São Paulo/Rio meaningfully higher, southern/southeastern hub cities
moderately higher, other northeastern cities close to Fortaleza) — not
sourced from a live cost-of-living API/dataset. Comparisons stay in USD
(the currency our salary/estimate figures are already in) rather than
converting to BRL, which would additionally require an FX-rate estimate
stacked on top of an already-approximate COL index.

Only produces a note when a specific city is named in the location text
and a numeric salary figure is available to compare — never guesses a
city, and never fabricates a number when neither is present.
"""

import re

# Relative to Fortaleza = 1.00. Rough/directional, not authoritative.
FORTALEZA_COL_INDEX = {
    "são paulo": 1.45,
    "sao paulo": 1.45,
    "rio de janeiro": 1.35,
    "brasília": 1.25,
    "brasilia": 1.25,
    "campinas": 1.30,
    "florianópolis": 1.25,
    "florianopolis": 1.25,
    "curitiba": 1.20,
    "porto alegre": 1.20,
    "belo horizonte": 1.15,
    "goiânia": 1.05,
    "goiania": 1.05,
    "recife": 1.05,
    "salvador": 1.05,
    "fortaleza": 1.00,
    "manaus": 0.95,
    "belém": 0.95,
    "belem": 0.95,
}

_DISPLAY_NAMES = {
    "são paulo": "São Paulo", "sao paulo": "São Paulo",
    "rio de janeiro": "Rio de Janeiro",
    "brasília": "Brasília", "brasilia": "Brasília",
    "campinas": "Campinas",
    "florianópolis": "Florianópolis", "florianopolis": "Florianópolis",
    "curitiba": "Curitiba",
    "porto alegre": "Porto Alegre",
    "belo horizonte": "Belo Horizonte",
    "goiânia": "Goiânia", "goiania": "Goiânia",
    "recife": "Recife",
    "salvador": "Salvador",
    "fortaleza": "Fortaleza",
    "manaus": "Manaus",
    "belém": "Belém", "belem": "Belém",
}

_SALARY_NUMBER_RE = re.compile(r"\$?([\d,]{4,})")


def find_city(location_text):
    """Return the canonical display name of a known Brazilian city
    mentioned in the location text, or None if no specific city is
    named (e.g. a bare "Remote, Brazil")."""
    if not location_text:
        return None
    text = location_text.lower()
    for key in sorted(_DISPLAY_NAMES, key=len, reverse=True):
        if key in text:
            return _DISPLAY_NAMES[key]
    return None


def col_index_for(city_display_name):
    for key, name in _DISPLAY_NAMES.items():
        if name == city_display_name:
            return FORTALEZA_COL_INDEX[key]
    return None


def parse_salary_figures(salary_text):
    """Pull (low, high, currency) out of a formatted salary/estimate
    string like "$65,000–$95,000 USD" or "Not disclosed". Returns None
    if no two numbers can be found."""
    if not salary_text or salary_text == "Not disclosed":
        return None
    numbers = [int(n.replace(",", "")) for n in _SALARY_NUMBER_RE.findall(salary_text)]
    if len(numbers) < 2:
        return None
    currency = "USD" if "USD" in salary_text or "$" in salary_text else ""
    return numbers[0], numbers[1], currency


def col_comparison_note(city, salary_text):
    """Build a plain-language cost-of-living note for `city` vs
    Fortaleza, using whatever numeric salary/estimate is available.
    Returns None if the city isn't Fortaleza-comparable, is Fortaleza
    itself, or no usable salary figure exists to compare."""
    if not city:
        return None
    index = col_index_for(city)
    if index is None or abs(index - 1.0) < 0.01:
        return None

    pct = round(abs(index - 1) * 100)
    direction = "higher" if index > 1 else "lower"
    base = f"{city}'s cost of living runs roughly {pct}% {direction} than Fortaleza (rough estimate)"

    figures = parse_salary_figures(salary_text)
    if not figures:
        return base + "."
    low, high, currency = figures
    fortaleza_low = int(round(low / index, -2))
    fortaleza_high = int(round(high / index, -2))
    return (
        f"{base} — ${low:,}–${high:,} {currency} there is roughly equivalent to "
        f"${fortaleza_low:,}–${fortaleza_high:,} {currency} of purchasing power in Fortaleza."
    )
