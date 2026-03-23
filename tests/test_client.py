"""Unit tests for AquiferClient — all HTTP calls are mocked via `responses`."""

import pytest
import responses as resp

from aquifer.client import AquiferClient, BASE_URL

from .conftest import (
    SAMPLE_BIBLE,
    SAMPLE_BIBLE_BOOK,
    SAMPLE_BIBLE_BOOK_TEXT,
    SAMPLE_GREEK_ALIGNMENT,
    SAMPLE_LANGUAGE,
    SAMPLE_SEARCH_RESULT,
    TEST_API_KEY,
)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_raises_on_empty_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        AquiferClient(api_key="")


def test_raises_on_none_api_key() -> None:
    with pytest.raises((ValueError, TypeError)):
        AquiferClient(api_key=None)  # type: ignore[arg-type]


def test_from_env_raises_when_var_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AQUIFER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="AQUIFER_API_KEY"):
        AquiferClient.from_env()


def test_from_env_reads_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AQUIFER_API_KEY", "my-key")
    client = AquiferClient.from_env()
    assert client._headers["api-key"] == "my-key"


def test_context_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import patch

    monkeypatch.setenv("AQUIFER_API_KEY", TEST_API_KEY)
    client = AquiferClient.from_env()
    with patch.object(client.session, "close") as mock_close:
        with client:
            assert client._headers["api-key"] == TEST_API_KEY
        mock_close.assert_called_once()


# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------


@resp.activate
def test_get_languages(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/languages", json=[SAMPLE_LANGUAGE])
    result = client.get_languages()
    assert len(result) == 1
    assert result[0]["code"] == "eng"


@resp.activate
def test_get_language_map(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/languages", json=[
        SAMPLE_LANGUAGE,
        {**SAMPLE_LANGUAGE, "id": 2, "code": "fra"},
    ])
    lang_map, languages = client.get_language_map()
    assert lang_map == {1: "eng", 2: "fra"}
    assert len(languages) == 2


@resp.activate
def test_get_languages_available_resources(client: AquiferClient) -> None:
    payload = [{"languageId": 1, "languageCode": "eng", "resourceCounts": [{"type": "Dictionary", "count": 5}]}]
    resp.add(resp.GET, f"{BASE_URL}/languages/available-resources", json=payload)
    result = client.get_languages_available_resources("MAT", start_chapter=1, end_chapter=1)
    assert result[0]["languageCode"] == "eng"
    assert resp.calls[0].request.url is not None
    assert "bookCode=MAT" in resp.calls[0].request.url


# ---------------------------------------------------------------------------
# Bibles
# ---------------------------------------------------------------------------


@resp.activate
def test_get_all_bibles(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles", json=[SAMPLE_BIBLE])
    result = client.get_all_bibles()
    assert result[0]["abbreviation"] == "BSB"


@resp.activate
def test_get_all_bibles_with_filters(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles", json=[SAMPLE_BIBLE])
    client.get_all_bibles(language_code="eng", has_greek_alignment=True)
    url = resp.calls[0].request.url
    assert "languageCode=eng" in url
    assert "hasGreekAlignment=True" in url


@resp.activate
def test_get_all_bible_books(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/books", json=[SAMPLE_BIBLE_BOOK])
    result = client.get_all_bible_books()
    assert result[0]["code"] == "MAT"


@resp.activate
def test_get_bible_books_undocumented(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/books", json=[SAMPLE_BIBLE_BOOK])
    result = client.get_bible_books(1)
    assert result[0]["code"] == "MAT"


@resp.activate
def test_get_bible_book_text(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/texts", json=SAMPLE_BIBLE_BOOK_TEXT)
    result = client.get_bible_book_text(1, "GEN")
    assert result["bookCode"] == "GEN"
    assert len(result["chapters"]) == 1


@resp.activate
def test_get_bible_book_text_with_audio(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/texts", json=SAMPLE_BIBLE_BOOK_TEXT)
    client.get_bible_book_text(1, "GEN", audio=True)
    assert "shouldReturnAudioData=True" in resp.calls[0].request.url


@resp.activate
def test_get_bible_book_text_passage_range(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/texts", json=SAMPLE_BIBLE_BOOK_TEXT)
    client.get_bible_book_text(1, "GEN", start_chapter=1, end_chapter=3)
    url = resp.calls[0].request.url
    assert "startChapter=1" in url
    assert "endChapter=3" in url


@resp.activate
def test_get_bible_greek_alignment(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/alignments/greek", json=SAMPLE_GREEK_ALIGNMENT)
    result = client.get_bible_greek_alignment(1, "MAT")
    assert result["bookCode"] == "MAT"
    assert result["chapters"][0]["verses"][0]["words"][0]["greekWords"][0]["lemma"] == "βίβλος"


@resp.activate
def test_get_bible_greek_alignment_sense_data(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/alignments/greek", json=SAMPLE_GREEK_ALIGNMENT)
    client.get_bible_greek_alignment(1, "MAT", sense_data=True)
    assert "shouldReturnSenseData=True" in resp.calls[0].request.url


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@resp.activate
def test_search_resources(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/resources/search", json=SAMPLE_SEARCH_RESULT)
    result = client.search_resources(language_code="eng", resource_collection_code="AquiferOpenBibleDictionary")
    assert result["totalItemCount"] == 1
    assert result["items"][0]["name"] == "Boaz"


@resp.activate
def test_search_resources_passage(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/resources/search", json=SAMPLE_SEARCH_RESULT)
    client.search_resources(book_code="RUT", start_chapter=2, start_verse=1, end_chapter=2, end_verse=1)
    url = resp.calls[0].request.url
    assert "bookCode=RUT" in url
    assert "startChapter=2" in url


@resp.activate
def test_get_resource(client: AquiferClient) -> None:
    payload = {
        "id": 42, "referenceId": 42, "name": "Boaz", "localizedName": "Boaz",
        "reviewLevel": "Professional", "content": "<p>Boaz was...</p>",
        "grouping": {"type": "Dictionary", "collectionCode": "AOBD", "collectionTitle": "AOBD", "associatedResources": []},
        "language": SAMPLE_LANGUAGE,
    }
    resp.add(resp.GET, f"{BASE_URL}/resources/42", json=payload)
    result = client.get_resource(42)
    assert result["name"] == "Boaz"
    assert "contentTextType=Html" in resp.calls[0].request.url


@resp.activate
def test_get_resource_available_languages(client: AquiferClient) -> None:
    payload = [{"contentId": 42, "contentDisplayName": "Boaz", "languageId": 1,
                "languageDisplayName": "English", "languageEnglishDisplayName": "English", "languageCode": "eng"}]
    resp.add(resp.GET, f"{BASE_URL}/resources/42/available-languages", json=payload)
    result = client.get_resource_available_languages(42)
    assert result[0]["languageCode"] == "eng"


@resp.activate
def test_get_resource_associations(client: AquiferClient) -> None:
    payload = {
        "passageAssociations": [{"startBookCode": "RUT", "startChapter": 2, "startVerse": 1,
                                  "endBookCode": "RUT", "endChapter": 2, "endVerse": 23}],
        "resourceAssociations": [],
    }
    resp.add(resp.GET, f"{BASE_URL}/resources/42/associations", json=payload)
    result = client.get_resource_associations(42)
    assert result["passageAssociations"][0]["startBookCode"] == "RUT"


@resp.activate
def test_get_resource_updates(client: AquiferClient) -> None:
    payload = {
        "returnedItemCount": 1, "totalItemCount": 1, "offset": 0,
        "items": [{"updateType": "New", "languageId": 1, "languageCode": "eng",
                   "resourceId": 99, "timestamp": "2026-01-01T00:00:00Z"}],
    }
    resp.add(resp.GET, f"{BASE_URL}/resources/updates", json=payload)
    result = client.get_resource_updates(start_timestamp="2026-01-01T00:00:00Z")
    assert result["items"][0]["updateType"] == "New"
    assert "startTimestamp" in resp.calls[0].request.url


@resp.activate
def test_get_resource_types(client: AquiferClient) -> None:
    payload = [{"type": "Dictionary", "collections": []}]
    resp.add(resp.GET, f"{BASE_URL}/resources/types", json=payload)
    result = client.get_resource_types()
    assert result[0]["type"] == "Dictionary"


@resp.activate
def test_get_resource_collections(client: AquiferClient) -> None:
    payload = [{"code": "AOBD", "displayName": "Aquifer Open Bible Dictionary",
                "shortName": "AOBD", "resourceType": "Dictionary", "sliCategory": None, "sliLevel": None}]
    resp.add(resp.GET, f"{BASE_URL}/resources/collections", json=payload)
    result = client.get_resource_collections()
    assert result[0]["code"] == "AOBD"


@resp.activate
def test_get_resource_collection(client: AquiferClient) -> None:
    payload = {
        "code": "AOBD", "displayName": "Aquifer Open Bible Dictionary",
        "shortName": "AOBD", "resourceType": "Dictionary", "sliCategory": None, "sliLevel": None,
        "licenseInfo": {"title": "MIT", "copyright": {"dates": None, "holder": {"name": "BibleAquifer", "url": ""}},
                        "licenses": [], "showAdaptationNoticeForEnglish": False,
                        "showAdaptationNoticeForNonEnglish": False},
        "availableLanguages": [{"languageId": 1, "languageCode": "eng", "displayName": "English", "resourceItemCount": 100}],
    }
    resp.add(resp.GET, f"{BASE_URL}/resources/collections/AOBD", json=payload)
    result = client.get_resource_collection("AOBD", language_codes=["eng"])
    assert result["availableLanguages"][0]["resourceItemCount"] == 100
    assert "languageCodes=eng" in resp.calls[0].request.url
