"""Shared test fixtures for aquifer-api-client tests."""

import pytest

from aquifer.client import AquiferClient

TEST_API_KEY = "test-api-key"
TEST_BASE_URL = "https://api2.aquifer.bible"


@pytest.fixture
def client() -> AquiferClient:
    """A client instance wired to a test API key (no real HTTP calls)."""
    return AquiferClient(api_key=TEST_API_KEY)


def page(page: int, total: int, per_page: int = 100) -> dict:
    """A v2 ``pagination`` block."""
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "has_more": page * per_page < total,
    }


LICENSE_INFO = {
    "title": "Aquifer Open License",
    "copyright": {"dates": "2024", "holder": {"name": "BiblioNexus", "url": "https://x"}},
    "licenses": [{"eng": {"name": "CC BY-SA 4.0", "url": "https://creativecommons.org"}}],
    "show_adaptation_notice_for_english": False,
    "show_adaptation_notice_for_non_english": True,
    "adaptation_notice": "<p>Adapted.</p>",
}

SAMPLE_LANGUAGE = {
    "language": "eng",
    "resource_count": 21,
    "name": "English",
    "localized_name": "English",
    "iso639_1": "en",
    "is_rtl": False,
    "word_locale": "en_US",
    "id": 1,
}

SAMPLE_BIBLE = {
    "resource_code": "BereanStandardBible",
    "name": "Berean Standard Bible",
    "abbreviation": "BSB",
    "language_code": "eng",
    "id": 1,
    "is_language_default": True,
    "has_audio": True,
    "has_alignments": True,
    "license_info": LICENSE_INFO,
}

SAMPLE_ARTICLE = {
    "resource_code": "AquiferOpenBibleDictionary",
    "language_code": "eng",
    "content_id": "3263",
    "title": "Aaron",
    "content": "<p>Brother of Moses</p>",
    "content_format": "html",
}

SAMPLE_UPDATE_ITEM = {
    "update_type": "updated",
    "language_code": "fra",
    "resource_code": "FIATranslationGuide",
    "content_id": "1004",
    "timestamp": "2026-09-01T00:00:00Z",
}
