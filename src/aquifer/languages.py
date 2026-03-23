"""ISO 639-3 language registry for languages supported by the Aquifer API."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageInfo:
    """Metadata for a single language."""

    iso639_3: str   # e.g. "eng"
    iso639_1: str   # e.g. "en"
    name: str       # English name, e.g. "English"
    is_rtl: bool


# Master registry — keyed by ISO 639-3 code
LANGUAGES: dict[str, LanguageInfo] = {
    "fra": LanguageInfo("fra", "fr", "French",                 False),
    "eng": LanguageInfo("eng", "en", "English",                False),
    "spa": LanguageInfo("spa", "es", "Spanish",                False),
    "hin": LanguageInfo("hin", "hi", "Hindi",                  False),
    "por": LanguageInfo("por", "pt", "Portuguese",             False),
    "arb": LanguageInfo("arb", "ar", "Arabic",                 True),
    "ind": LanguageInfo("ind", "id", "Indonesian",             False),
    "rus": LanguageInfo("rus", "ru", "Russian",                False),
    "swh": LanguageInfo("swh", "sw", "Swahili",                False),
    "zht": LanguageInfo("zht", "zh", "Chinese (Traditional)",  False),
    "zhs": LanguageInfo("zhs", "zh", "Chinese (Simplified)",   False),
    "nld": LanguageInfo("nld", "nl", "Dutch",                  False),
    "apd": LanguageInfo("apd", "ar", "Sudanese Arabic",        True),
    "nep": LanguageInfo("nep", "ne", "Nepali",                 False),
    "tpi": LanguageInfo("tpi", "png", "Tok Pisin",             False),
    "zlm": LanguageInfo("zlm", "my", "Malay",                  False),
    "hau": LanguageInfo("hau", "ha", "Hausa",                  False),
    "ibo": LanguageInfo("ibo", "ig", "Igbo",                   False),
    "bis": LanguageInfo("bis", "bi", "Bislama",                False),
    "vie": LanguageInfo("vie", "vi", "Vietnamese",             False),
    "fas": LanguageInfo("fas", "fa", "Farsi (Persian)",        True),
    "jpn": LanguageInfo("jpn", "ja", "Japanese",               False),
    "grc": LanguageInfo("grc", "el", "Greek",                  False),
    "heb": LanguageInfo("heb", "he", "Hebrew",                 True),
}


def get_language(code: str) -> LanguageInfo | None:
    """Look up language info by ISO 639-3 code. Returns None if not found."""
    return LANGUAGES.get(code)


def is_rtl(code: str) -> bool:
    """Return True if the language with the given ISO 639-3 code is right-to-left."""
    lang = LANGUAGES.get(code)
    return lang.is_rtl if lang else False
