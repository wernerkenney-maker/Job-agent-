#!/usr/bin/env python3
"""Rough cost-of-living comparison against Fortaleza (the candidate's home
base) for Brazilian cities mentioned in a posting's location.

FORTALEZA_COL_INDEX is a rough, directional index (Fortaleza = 1.00),
based on general knowledge of regional cost-of-living variance in Brazil
(São Paulo/Rio meaningfully higher, southern/southeastern hub cities
moderately higher, other northeastern cities close to Fortaleza) — not
sourced from a live cost-of-living API/dataset.

Two comparison paths, depending on what currency the salary figure is
already in:
- International-market matches carry USD figures, so producing a reais
  comparison also requires an approximate USD/BRL rate
  (USD_TO_BRL_RATE) — also illustrative, not a live quote, and stacks on
  top of the already-approximate COL index.
- Brazilian-market matches (Gupy-sourced) are already BRL, monthly (the
  normal way Brazilian salaries are quoted/reported) — no FX conversion
  needed, just the COL ratio.
Both approximations are called out in the note text itself.

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
    "itapevi": 1.30,
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
    "itapevi": "Itapevi",
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
_BRL_NUMBER_RE = re.compile(r"R\$\s*([\d.]{4,})")

# Illustrative only -- not a live quote, and exchange rates move. Rough
# midpoint of recent USD/BRL levels; revisit if it drifts noticeably.
USD_TO_BRL_RATE = 5.00


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
    """Pull (low, high, currency) out of a formatted USD salary/estimate
    string like "$65,000–$95,000 USD" or "Not disclosed". Returns None
    if no two numbers can be found."""
    if not salary_text or salary_text == "Not disclosed":
        return None
    numbers = [int(n.replace(",", "")) for n in _SALARY_NUMBER_RE.findall(salary_text)]
    if len(numbers) < 2:
        return None
    currency = "USD" if "USD" in salary_text or "$" in salary_text else ""
    return numbers[0], numbers[1], currency


def parse_brl_salary_figures(salary_text):
    """Pull (low, high) monthly BRL figures out of a formatted string like
    "R$4.500–R$9.800/month (estimated -- ...)" (dots are Brazilian
    thousands separators, not decimals). Returns None if fewer than two
    numbers are found."""
    if not salary_text or salary_text == "Not disclosed":
        return None
    numbers = [int(n.replace(".", "")) for n in _BRL_NUMBER_RE.findall(salary_text)]
    if len(numbers) < 2:
        return None
    return numbers[0], numbers[1]


def format_brl(amount):
    return "R$" + f"{amount:,.0f}".replace(",", ".")


def _col_clause(city, index):
    pct = round(abs(index - 1) * 100)
    direction = "higher" if index > 1 else "lower"
    return f"{city}'s cost of living runs roughly {pct}% {direction} than Fortaleza"


def col_comparison_note(city, salary_text):
    """USD-denominated match (international-market): build a
    plain-language, reais-denominated cost-of-living note for `city` vs
    Fortaleza. Returns None if the city isn't Fortaleza-comparable, is
    Fortaleza itself, or no usable salary figure exists to compare."""
    if not city:
        return None
    index = col_index_for(city)
    if index is None or abs(index - 1.0) < 0.01:
        return None

    col_clause = _col_clause(city, index)

    figures = parse_salary_figures(salary_text)
    if not figures:
        return f"{col_clause} (rough estimate)."

    low, high, currency = figures
    if currency != "USD":
        return f"{col_clause} (rough estimate)."

    low_brl = low * USD_TO_BRL_RATE
    high_brl = high * USD_TO_BRL_RATE
    fortaleza_low_brl = round(low_brl / index, -3)
    fortaleza_high_brl = round(high_brl / index, -3)

    return (
        f"~{format_brl(low_brl)}–{format_brl(high_brl)} in {city} is roughly equivalent to "
        f"~{format_brl(fortaleza_low_brl)}–{format_brl(fortaleza_high_brl)} of purchasing power in "
        f"Fortaleza ({col_clause}; both figures rough estimates, using an approximate "
        f"R${USD_TO_BRL_RATE:.2f}/USD exchange rate)."
    )


def col_comparison_note_brl(city, low_brl, high_brl, period_label="/month"):
    """Already-BRL match (Brazilian-market, e.g. Gupy): same comparison,
    but no FX conversion needed since the figures are already reais.
    `low_brl`/`high_brl` should be monthly figures (the normal way
    Brazilian salaries are quoted)."""
    if not city:
        return None
    index = col_index_for(city)
    if index is None or abs(index - 1.0) < 0.01:
        return None

    col_clause = _col_clause(city, index)
    fortaleza_low = round(low_brl / index, -2)
    fortaleza_high = round(high_brl / index, -2)

    return (
        f"~{format_brl(low_brl)}–{format_brl(high_brl)}{period_label} in {city} is roughly "
        f"equivalent to ~{format_brl(fortaleza_low)}–{format_brl(fortaleza_high)}{period_label} "
        f"of purchasing power in Fortaleza ({col_clause}; both figures rough estimates)."
    )
