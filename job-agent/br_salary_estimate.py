#!/usr/bin/env python3
"""Salary estimates for Brazilian-market (Gupy-sourced) postings, which
never structurally disclose pay (unlike some international postings, no
Brazilian job board in this pipeline exposes a salary field at all).

Grounded in real reference data pulled from Glassdoor Brasil salary pages
for each title cluster (searched at build time, see README) rather than
pure model inference — per the user's request, this is checked against
real reference sites, not guessed from scratch. Always labeled as an
estimate; Brazilian salaries are conventionally quoted monthly (not
annualized), so figures here follow that convention.

This is deliberately a small, title-keyword-matched table rather than a
live scrape of Glassdoor/Salario.com.br on every run (those sites require
a browser session and block simple scraping) -- revisit a title's range
here if the market moves noticeably.
"""

import re

# Brazilian job titles abbreviate "sênior" as "Sr" (and "pleno"/mid-level
# as "Pl") at least as often as spelling it out.
_SENIOR = r"(?:s[eê]nior|\bsr\b)"

# (pattern, low_monthly_brl, high_monthly_brl, source note), first match
# wins -- ordered most-specific first. Figures are monthly BRL, grounded
# in Glassdoor Brasil salary pages for each title cluster.
_BANDS = [
    (re.compile(rf"gerente.*(pesquisa cl[ií]nica|projetos cl[ií]nicos)", re.I),
     14000, 19000, "Glassdoor Brazil, Gerente de Pesquisa Clínica (São Paulo)"),
    (re.compile(r"coordenador.*(pesquisa cl[ií]nica|centro de pesquisa)", re.I),
     4500, 9800, "Glassdoor Brazil, Coordenador de Pesquisa Clínica (São Paulo range)"),
    (re.compile(r"coordenador.*planejamento|planejamento.*coordenador", re.I),
     6000, 12000, "Glassdoor Brazil, Coordenador de Planejamento (general/pharma, non-clinical)"),
    (re.compile(rf"(monitor|\bcra\b).*{_SENIOR}|{_SENIOR}.*(monitor|\bcra\b)", re.I),
     9500, 13200, "Glassdoor Brazil, Monitor de Pesquisa Clínica Sênior (ICON reference)"),
    (re.compile(r"(monitor|\bcra\b)", re.I),
     5300, 9500, "Glassdoor Brazil, Monitor de Pesquisa Clínica / CRA (junior-mid band)"),
    (re.compile(rf"farmacovigil[aâ]ncia.*{_SENIOR}|{_SENIOR}.*farmacovigil[aâ]ncia", re.I),
     7800, 14800, "Glassdoor Brazil, Analista de Farmacovigilância Sênior"),
    (re.compile(r"farmacovigil[aâ]ncia", re.I),
     5000, 8000, "Glassdoor Brazil, Analista de Farmacovigilância (below senior band)"),
    (re.compile(rf"assuntos regulat[oó]rios.*{_SENIOR}|{_SENIOR}.*regulat[oó]rios", re.I),
     8000, 11200, "Glassdoor Brazil, Analista de Assuntos Regulatórios Sênior"),
    (re.compile(r"assuntos regulat[oó]rios|regulat[oó]rios e start up", re.I),
     5000, 7500, "Glassdoor Brazil, Analista de Assuntos Regulatórios (below senior band)"),
    (re.compile(rf"qualidade.*pesquisa cl[ií]nica.*{_SENIOR}|{_SENIOR}.*qualidade.*pesquisa", re.I),
     6800, 10500, "Glassdoor Brazil, Analista de Pesquisa Clínica Sênior band (quality function)"),
    (re.compile(rf"(pesquisa cl[ií]nica|projetos cl[ií]nicos).*{_SENIOR}|{_SENIOR}.*(pesquisa cl[ií]nica|projetos cl[ií]nicos)", re.I),
     6800, 10500, "Glassdoor Brazil, Analista de Pesquisa Clínica Sênior"),
    (re.compile(r"data management", re.I),
     8000, 13000, "Glassdoor Brazil, senior specialist band, pharma/CRO data functions"),
    (re.compile(r"pesquisa cl[ií]nica", re.I),
     3500, 6500, "Glassdoor Brazil, Analista de Pesquisa Clínica (non-senior)"),
]

_DEFAULT_BAND = (4000, 8000, "Glassdoor Brazil, general clinical-research analyst band")


def estimate_br_salary(title):
    for pattern, low, high, note in _BANDS:
        if pattern.search(title):
            return format_br_estimate(low, high, note)
    low, high, note = _DEFAULT_BAND
    return format_br_estimate(low, high, note)


def format_br_estimate(low, high, note):
    from cost_of_living import format_brl
    return f"{format_brl(low)}–{format_brl(high)}/month (estimated — {note}, not disclosed by employer)"
