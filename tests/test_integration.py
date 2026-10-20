"""Integration tests — make real calls to the Aquifer v2 API.

These tests are skipped automatically when ``AQUIFER_API_KEY`` is not set.
Run them with::

    pytest -m integration

or deselect them (default) with::

    pytest -m "not integration"
"""

import itertools
import os

import pytest

from aquifer.client import AquiferAPIError, AquiferClient

pytestmark = pytest.mark.integration

DICT = "AquiferOpenBibleDictionary"
BSB = "BereanStandardBible"


@pytest.fixture(scope="module")
def client() -> AquiferClient:
    api_key = os.getenv("AQUIFER_API_KEY")
    if not api_key:
        pytest.skip("AQUIFER_API_KEY not set")
    return AquiferClient.from_env()


def test_get_languages(client: AquiferClient) -> None:
    languages = client.get_languages()["languages"]
    assert "eng" in {lang["language"] for lang in languages}


def test_resource_catalog(client: AquiferClient) -> None:
    body = client.get_resources(language="eng", per_page=5)
    assert body["resources"]
    assert body["pagination"]["per_page"] == 5


def test_get_resource_types(client: AquiferClient) -> None:
    body = client.get_resource_types(group_by="aquifer_type")
    assert body["group_by"] == "aquifer_type"
    assert body["types"]


def test_get_resource_and_language_detail(client: AquiferClient) -> None:
    detail = client.get_resource(DICT)
    assert any(lang["language"] == "eng" for lang in detail["available_languages"])
    assert client.get_resource_language(DICT, "eng")["language"] == "eng"


def test_unknown_resource_gives_suggestions(client: AquiferClient) -> None:
    with pytest.raises(AquiferAPIError) as exc:
        client.get_resource("AquiferOpenBibleDictionry")
    assert exc.value.status_code == 404


def test_renamed_resource_code_resolves(client: AquiferClient) -> None:
    assert client.get_resource("TyndaleBibleDictionary")["resource_code"] == DICT


def test_get_resource_files(client: AquiferClient) -> None:
    assert "files" in client.get_resource_files(DICT, "eng")


def test_search_articles(client: AquiferClient) -> None:
    body = client.search_articles("Aaron", language="eng")
    assert body["results"]


def test_article_roundtrip(client: AquiferClient) -> None:
    hit = client.search_articles("Aaron", language="eng", resource_code=DICT)["results"][0]
    article = client.get_article(DICT, "eng", hit["content_id"], content_format="markdown")
    assert article["title"]
    assert isinstance(article["content"], str)
    assoc = client.get_article_associations(DICT, "eng", hit["content_id"])
    assert "passage_associations" in assoc
    assert "available_languages" in client.get_article_available_languages(
        DICT, "eng", hit["content_id"]
    )


def test_bulk_articles(client: AquiferClient) -> None:
    body = client.get_articles(DICT, "eng", include="none", per_page=3)
    assert len(body["articles"]) <= 3
    assert "content" not in body["articles"][0]
    assert (
        len(list(itertools.islice(client.iter_articles(DICT, "eng", include="none"), 150))) == 150
    )
    assert client.get_license_info(DICT, "eng")["title"]


def test_resource_updates(client: AquiferClient) -> None:
    since = "2026-01-01T00:00:00Z"
    total = client.count_resource_updates(since, resource_code=DICT, language_code="eng")
    assert total >= 0
    first = list(itertools.islice(client.iter_resource_updates(since, resource_code=DICT), 3))
    assert all(item["resource_code"] == DICT for item in first)


def test_passage_endpoints(client: AquiferClient) -> None:
    arts = client.get_passage_articles("GEN 1:1", resource_type="Study Notes", per_page=5)
    assert arts["articles"]
    counts = client.get_passage_resource_counts("JHN 3", languages="eng")
    assert counts["languages"][0]["language"] == "eng"


def test_passage_tokens(client: AquiferClient) -> None:
    body = client.get_passage_tokens("GEN 1:1", BSB, include_alignment=True)
    assert body["tokens"]
    assert "alignment" in body


def test_bibles_and_text(client: AquiferClient) -> None:
    bibles = client.get_bibles(language="eng", has_alignments=True)["bibles"]
    assert any(b["resource_code"] == BSB for b in bibles)
    assert client.get_bible_books()["books"][0]["usfm_code"] == "GEN"
    text = client.get_bible_text(BSB, "RUT 1:1-2", should_return_audio_data=True)
    assert text["chapters"][0]["verses"]
    by_book = client.get_bible_text(BSB, book_code="RUT", start_chapter=1, end_chapter=1)
    assert by_book["book_code"] == "RUT"


def test_bible_verses_batch(client: AquiferClient) -> None:
    body = client.get_bible_verses(BSB, ["GEN 1:1", "JHN 3:16", "GEN 99:1"])
    assert [v["ref"] for v in body["verses"]] == ["GEN 1:1", "JHN 3:16"]
    assert body["missing"] == ["GEN 99:1"]


def test_acai(client: AquiferClient) -> None:
    assert client.get_acai_types()["types"]
    entity = client.get_acai_entity("person:Aaron")
    assert entity["acai_id"] == "person:Aaron"
    assert client.get_acai_references("person:Aaron", per_page=3)["references"]
    assert client.get_acai_articles("person:Aaron", min_confidence=0.8, per_page=3)["articles"]
    assert client.get_acai_entities(type="person", per_page=3)["entities"]
    speeches = client.get_acai_speeches("person:Aaron", per_page=1)["speeches"]
    token_id = client.get_acai_tokens("person:Aaron", per_page=1)["tokens"][0]["token_id"]
    assert client.get_token(token_id)["token_id"] == token_id
    assert isinstance(speeches, list)
