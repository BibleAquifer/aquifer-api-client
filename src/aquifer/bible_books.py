"""Bible book reference data for use with the Aquifer API.

All book codes are USFM 3-letter identifiers as used by the API (e.g. ``"MAT"``).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Book sets
# ---------------------------------------------------------------------------

OT_BOOKS: frozenset[str] = frozenset([
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT",
    "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH",
    "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER",
    "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
    "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
])

NT_BOOKS: frozenset[str] = frozenset([
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO",
    "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI",
    "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
])

APOCRYPHA_BOOKS: frozenset[str] = frozenset([
    "TOB", "JDT", "ESG", "WIS", "SIR", "BAR", "LJE", "S3Y",
    "SUS", "BEL", "1MA", "2MA", "3MA", "4MA", "1ES", "2ES",
    "MAN", "PS2", "ODA", "PSS",
])

# ---------------------------------------------------------------------------
# Canonical book order (OT then NT, 66 books)
# ---------------------------------------------------------------------------

USFM_BOOK_CODES: list[str] = [
    # Old Testament
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT",
    "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH",
    "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER",
    "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
    "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
    # New Testament
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO",
    "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI",
    "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
]

# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def book_is_ot(usfm_code: str) -> bool:
    """Return True if *usfm_code* is an Old Testament book."""
    return usfm_code in OT_BOOKS


def book_is_nt(usfm_code: str) -> bool:
    """Return True if *usfm_code* is a New Testament book."""
    return usfm_code in NT_BOOKS


def book_is_apocrypha(usfm_code: str) -> bool:
    """Return True if *usfm_code* is a deuterocanonical / Apocrypha book."""
    return usfm_code in APOCRYPHA_BOOKS


def canonical_order(usfm_code: str) -> int:
    """Return the 0-based canonical position of *usfm_code*, or -1 if unknown."""
    try:
        return USFM_BOOK_CODES.index(usfm_code)
    except ValueError:
        return -1
