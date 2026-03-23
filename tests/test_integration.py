"""Integration tests — make real calls to the Aquifer API.

These tests are skipped automatically when ``AQUIFER_API_KEY`` is not set.
Run them with::

    pytest -m integration

or deselect them (default) with::

    pytest -m "not integration"
"""

import os

import pytest

from aquifer.client import AquiferClient


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client() -> AquiferClient:
    api_key = os.getenv("AQUIFER_API_KEY")
    if not api_key:
        pytest.skip("AQUIFER_API_KEY not set")
    return AquiferClient(api_key=api_key)


# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------


def test_get_languages(client: AquiferClient) -> None:
    languages = client.get_languages()
    assert len(languages) > 0
    codes = {lang["code"] for lang in languages}
    assert "eng" in codes


def test_get_language_map(client: AquiferClient) -> None:
    lang_map, languages = client.get_language_map()
    assert isinstance(lang_map, dict)
    assert len(lang_map) == len(languages)
    assert all(isinstance(k, int) for k in lang_map)


def test_get_languages_available_resources(client: AquiferClient) -> None:
    result = client.get_languages_available_resources("RUT", start_chapter=1, end_chapter=4)
    assert isinstance(result, list)
    assert all("languageCode" in item for item in result)


# ---------------------------------------------------------------------------
# Bibles
# ---------------------------------------------------------------------------


def test_get_all_bibles(client: AquiferClient) -> None:
    bibles = client.get_all_bibles()
    assert len(bibles) > 0
    assert all("abbreviation" in b for b in bibles)


def test_get_all_bibles_filtered(client: AquiferClient) -> None:
    bibles = client.get_all_bibles(language_code="eng", has_greek_alignment=True)
    assert all(b["hasGreekAlignment"] for b in bibles)


def test_get_all_bible_books(client: AquiferClient) -> None:
    books = client.get_all_bible_books()
    codes = {b["code"] for b in books}
    assert "GEN" in codes
    assert "REV" in codes


def test_get_bible_book_text(client: AquiferClient) -> None:
    bibles = client.get_all_bibles(language_code="eng", is_language_default=True)
    assert bibles, "No default English Bible found"
    bible_id = bibles[0]["id"]
    text = client.get_bible_book_text(bible_id, "RUT")
    assert text["bookCode"] == "RUT"
    assert len(text["chapters"]) == 4


def test_get_bible_book_text_passage_range(client: AquiferClient) -> None:
    bibles = client.get_all_bibles(language_code="eng", is_language_default=True)
    bible_id = bibles[0]["id"]
    text = client.get_bible_book_text(bible_id, "RUT", start_chapter=1, end_chapter=1)
    assert len(text["chapters"]) == 1


def test_get_bible_greek_alignment(client: AquiferClient) -> None:
    bibles = client.get_all_bibles(language_code="eng", has_greek_alignment=True)
    assert bibles, "No Bible with Greek alignment found"
    bible_id = bibles[0]["id"]
    alignment = client.get_bible_greek_alignment(bible_id, "RUT", start_chapter=1, end_chapter=1)
    assert alignment["bookCode"] == "RUT"
    assert len(alignment["chapters"]) >= 1


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


def test_search_resources_by_collection(client: AquiferClient) -> None:
    result = client.search_resources(
        language_code="eng",
        resource_collection_code="AquiferOpenBibleDictionary",
        limit=5,
    )
    assert result["totalItemCount"] > 0
    assert len(result["items"]) <= 5


def test_search_resources_by_passage(client: AquiferClient) -> None:
    result = client.search_resources(
        book_code="RUT",
        start_chapter=2, end_chapter=2,
        start_verse=1, end_verse=1,
        language_code="eng",
        limit=10,
    )
    assert isinstance(result["totalItemCount"], int)


def test_get_resource(client: AquiferClient) -> None:
    result = client.search_resources(
        language_code="eng",
        resource_collection_code="AquiferOpenBibleDictionary",
        limit=1,
    )
    assert result["items"], "No resources returned"
    content_id = result["items"][0]["id"]
    resource = client.get_resource(content_id, text_type="Html")
    assert resource["id"] == content_id
    assert "content" in resource


def test_get_resource_available_languages(client: AquiferClient) -> None:
    result = client.search_resources(
        language_code="eng",
        resource_collection_code="AquiferOpenBibleDictionary",
        limit=1,
    )
    content_id = result["items"][0]["id"]
    langs = client.get_resource_available_languages(content_id)
    assert isinstance(langs, list)
    assert any(lang["languageCode"] == "eng" for lang in langs)


def test_get_resource_associations(client: AquiferClient) -> None:
    result = client.search_resources(
        language_code="eng",
        resource_collection_code="AquiferOpenBibleDictionary",
        limit=1,
    )
    content_id = result["items"][0]["id"]
    assoc = client.get_resource_associations(content_id)
    assert "passageAssociations" in assoc
    assert "resourceAssociations" in assoc


def test_get_resource_updates(client: AquiferClient) -> None:
    result = client.get_resource_updates(
        start_timestamp="2024-01-01T00:00:00Z",
        resource_collection_code="AquiferOpenBibleDictionary",
        limit=10,
    )
    assert "totalItemCount" in result
    assert isinstance(result["items"], list)


def test_get_resource_types(client: AquiferClient) -> None:
    types = client.get_resource_types()
    assert len(types) > 0
    type_names = {t["type"] for t in types}
    assert "Dictionary" in type_names or len(type_names) > 0


def test_get_resource_collections(client: AquiferClient) -> None:
    collections = client.get_resource_collections()
    codes = {c["code"] for c in collections}
    assert "AquiferOpenBibleDictionary" in codes


def test_get_resource_collection(client: AquiferClient) -> None:
    detail = client.get_resource_collection("AquiferOpenBibleDictionary")
    assert detail["code"] == "AquiferOpenBibleDictionary"
    assert len(detail["availableLanguages"]) > 0
