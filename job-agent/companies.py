#!/usr/bin/env python3
"""Corporate-family mapping shared across job board providers (Greenhouse,
Lever, ...), used by dedup.py to merge sibling postings of the same role
posted to more than one board by the same company group."""

COMPANY_FAMILIES = {
    "Precision Medicine Group": "Precision Medicine Group family",
    "Precision for Medicine": "Precision Medicine Group family",
    "Precision AQ": "Precision Medicine Group family",
}
