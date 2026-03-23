"""Shared test fixtures for aquifer-api-client tests."""

import pytest

from aquifer.client import AquiferClient

TEST_API_KEY = "test-api-key"
TEST_BASE_URL = "https://api.aquifer.bible"


@pytest.fixture
def client() -> AquiferClient:
    """A client instance wired to a test API key (no real HTTP calls)."""
    return AquiferClient(api_key=TEST_API_KEY)


# ---------------------------------------------------------------------------
# Sample payloads — used by multiple test modules
# ---------------------------------------------------------------------------

SAMPLE_LANGUAGE = {
    "id": 1,
    "code": "eng",
    "englishDisplay": "English",
    "localizedDisplay": "English",
    "scriptDirection": "LTR",
}

SAMPLE_BIBLE = {
    "id": 1,
    "name": "Berean Standard Bible",
    "abbreviation": "BSB",
    "languageId": 1,
    "isLanguageDefault": True,
    "hasAudio": True,
    "hasGreekAlignment": True,
    "licenseInfo": {
        "title": "BSB License",
        "copyright": {"dates": "2016-2024", "holder": {"name": "Bible Hub", "url": "https://biblehub.com"}},
        "licenses": [{"eng": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}}],
    },
}

SAMPLE_BIBLE_BOOK = {"name": "Matthew", "code": "MAT"}

SAMPLE_VERSE = {"number": 1, "text": "In the beginning God created the heavens and the earth."}

SAMPLE_CHAPTER = {"number": 1, "verses": [SAMPLE_VERSE]}

SAMPLE_BIBLE_BOOK_TEXT = {
    "bibleId": 1,
    "bibleName": "Berean Standard Bible",
    "bibleAbbreviation": "BSB",
    "bookName": "Genesis",
    "bookCode": "GEN",
    "chapters": [SAMPLE_CHAPTER],
}

SAMPLE_GREEK_WORD = {
    "word": "Βίβλος",
    "grammarType": "noun",
    "usageCode": "N-NSF",
    "lemma": "βίβλος",
    "strongsNumber": "G0976",
}

SAMPLE_ALIGNMENT_WORD = {
    "number": 1,
    "word": "This",
    "nextWordIsInGroup": True,
    "greekWords": [SAMPLE_GREEK_WORD],
}

SAMPLE_ALIGNMENT_VERSE = {"number": 1, "words": [SAMPLE_ALIGNMENT_WORD]}

SAMPLE_ALIGNMENT_CHAPTER = {"number": 1, "verses": [SAMPLE_ALIGNMENT_VERSE]}

SAMPLE_GREEK_ALIGNMENT = {
    "bibleId": 1,
    "bibleName": "Berean Standard Bible",
    "bibleAbbreviation": "BSB",
    "greekBibleAbbreviation": "SBLGNT",
    "bookName": "Matthew",
    "bookCode": "MAT",
    "chapters": [SAMPLE_ALIGNMENT_CHAPTER],
}

SAMPLE_RESOURCE_SUMMARY = {
    "id": 42,
    "name": "Boaz",
    "localizedName": "Boaz",
    "reviewLevel": "Professional",
    "mediaType": "Text",
    "languageCode": "eng",
    "grouping": {
        "type": "Dictionary",
        "collectionCode": "AquiferOpenBibleDictionary",
        "collectionTitle": "Aquifer Open Bible Dictionary",
    },
}

SAMPLE_SEARCH_RESULT = {
    "totalItemCount": 1,
    "returnedItemCount": 1,
    "offset": 0,
    "items": [SAMPLE_RESOURCE_SUMMARY],
}
