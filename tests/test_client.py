"""Unit tests for AquiferClient — all HTTP calls are mocked via `responses`."""

from urllib.parse import parse_qs, urlparse

import pytest
import requests
import responses as resp

from aquifer import RESOURCE_CODE_RENAMES, current_resource_code
from aquifer.client import BASE_URL, AquiferAPIError, AquiferClient

from .conftest import (
    LICENSE_INFO,
    SAMPLE_ARTICLE,
    SAMPLE_BIBLE,
    SAMPLE_LANGUAGE,
    SAMPLE_UPDATE_ITEM,
    TEST_API_KEY,
    page,
)


def last_query() -> dict[str, list[str]]:
    return parse_qs(urlparse(resp.calls[-1].request.url).query)


def last_path() -> str:
    return urlparse(resp.calls[-1].request.url).path


# ---------------------------------------------------------------------------
# Construction, transport and errors
# ---------------------------------------------------------------------------


def test_default_base_url_is_v2() -> None:
    assert BASE_URL == "https://api2.aquifer.bible"


def test_raises_on_empty_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        AquiferClient(api_key="")


def test_from_env_raises_when_var_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AQUIFER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="AQUIFER_API_KEY"):
        AquiferClient.from_env()


def test_from_env_reads_key_and_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AQUIFER_API_KEY", "k")
    monkeypatch.setenv("AQUIFER_API_BASE_URL", "http://127.0.0.1:8000/")
    c = AquiferClient.from_env()
    assert c._headers == {"api-key": "k"}
    assert c.base_url == "http://127.0.0.1:8000"


def test_from_env_default_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AQUIFER_API_KEY", "k")
    monkeypatch.delenv("AQUIFER_API_BASE_URL", raising=False)
    assert AquiferClient.from_env().base_url == BASE_URL


def test_context_manager_closes_session() -> None:
    with AquiferClient(api_key="k") as c:
        assert isinstance(c, AquiferClient)


@resp.activate
def test_sends_api_key_header_and_drops_none_params(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/languages", json={"languages": [SAMPLE_LANGUAGE]})
    client.get_languages()
    assert resp.calls[0].request.headers["api-key"] == TEST_API_KEY


@resp.activate
def test_bool_params_are_lowercase(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles", json={"bibles": [], "pagination": page(1, 0)})
    client.get_bibles(has_audio=True, has_alignments=False)
    assert last_query() == {"has_audio": ["true"], "has_alignments": ["false"]}


@resp.activate
def test_http_error_carries_detail(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/Typo",
        status=404,
        json={"detail": "unknown resource", "did_you_mean": ["TypoFree"]},
    )
    with pytest.raises(AquiferAPIError) as exc:
        client.get_resource("Typo")
    assert exc.value.status_code == 404
    assert exc.value.did_you_mean == ["TypoFree"]
    assert isinstance(exc.value, requests.HTTPError)


@resp.activate
def test_non_json_error_body(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/languages", status=401, body="nope")
    with pytest.raises(AquiferAPIError) as exc:
        client.get_languages()
    assert exc.value.detail is None
    assert exc.value.did_you_mean == []


@resp.activate
def test_rate_limit_headers_recorded(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/languages",
        json={"languages": []},
        headers={"RateLimit-Limit": "25", "RateLimit-Remaining": "24", "RateLimit-Reset": "1"},
    )
    client.get_languages()
    assert client.rate_limit == {
        "RateLimit-Limit": "25",
        "RateLimit-Remaining": "24",
        "RateLimit-Reset": "1",
    }


@resp.activate
def test_deprecation_header_logs_warning(
    client: AquiferClient, caplog: pytest.LogCaptureFixture
) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/TyndaleStudyNotes",
        json={"resource_code": "AquiferOpenStudyNotes"},
        headers={
            "Deprecation": "true",
            "Link": '</resources/AquiferOpenStudyNotes>; rel="successor-version"',
        },
    )
    with caplog.at_level("WARNING"):
        client.get_resource("TyndaleStudyNotes")
    assert "deprecated" in caplog.text


def test_resource_code_renames() -> None:
    assert current_resource_code("TyndaleBibleDictionary") == "AquiferOpenBibleDictionary"
    assert current_resource_code("UbsImages") == "UBSImages"
    assert current_resource_code("AquiferOpenStudyNotes") == "AquiferOpenStudyNotes"
    assert len(RESOURCE_CODE_RENAMES) == 8


# ---------------------------------------------------------------------------
# Languages and resources
# ---------------------------------------------------------------------------


@resp.activate
def test_get_languages(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/languages", json={"languages": [SAMPLE_LANGUAGE]})
    assert client.get_languages()["languages"][0]["language"] == "eng"


@resp.activate
def test_get_resources_and_iter_follow_pages(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources",
        json={"language": None, "resources": [{"resource_code": "A"}], "pagination": page(1, 2, 1)},
    )
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources",
        json={"language": None, "resources": [{"resource_code": "B"}], "pagination": page(2, 2, 1)},
    )
    codes = [r["resource_code"] for r in client.iter_resources(language="eng")]
    assert codes == ["A", "B"]
    assert resp.calls[0].request.url.endswith("language=eng&page=1&per_page=500")
    assert "page=2" in resp.calls[1].request.url


@resp.activate
def test_get_resource_types(client: AquiferClient) -> None:
    resp.add(
        resp.GET, f"{BASE_URL}/resources/types", json={"group_by": "aquifer_type", "types": []}
    )
    client.get_resource_types(group_by="aquifer_type")
    assert last_query() == {"group_by": ["aquifer_type"]}


@resp.activate
def test_search_articles_params(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/search",
        json={"query": "Aaron", "results": [], "pagination": page(1, 0)},
    )
    client.search_articles(
        "Aaron", book_code="GEN", start_chapter=1, content_order=["canonical", "alphabetical"]
    )
    assert last_query() == {
        "query": ["Aaron"],
        "book_code": ["GEN"],
        "start_chapter": ["1"],
        "content_order": ["canonical,alphabetical"],
    }


@resp.activate
def test_iter_search_articles(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/search",
        json={"query": "a", "results": [{"content_id": "1"}], "pagination": page(1, 1)},
    )
    assert [r["content_id"] for r in client.iter_search_articles("Aar", resource_code="X")] == ["1"]
    assert last_query()["resource_code"] == ["X"]


@resp.activate
def test_get_resource_updates(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/updates",
        json={
            "returned_item_count": 1,
            "total_item_count": 1,
            "offset": 0,
            "items": [SAMPLE_UPDATE_ITEM],
        },
    )
    body = client.get_resource_updates("2026-01-01T00:00:00Z", language_code="fra", limit=10)
    assert body["items"][0]["update_type"] == "updated"
    assert last_query() == {
        "start_timestamp": ["2026-01-01T00:00:00Z"],
        "language_code": ["fra"],
        "limit": ["10"],
    }


@resp.activate
def test_iter_resource_updates_pages_by_offset(client: AquiferClient) -> None:
    def feed(offset: int, n: int) -> dict:
        return {
            "returned_item_count": n,
            "total_item_count": 3,
            "offset": offset,
            "items": [SAMPLE_UPDATE_ITEM] * n,
        }

    resp.add(resp.GET, f"{BASE_URL}/resources/updates", json=feed(0, 2))
    resp.add(resp.GET, f"{BASE_URL}/resources/updates", json=feed(2, 1))
    assert len(list(client.iter_resource_updates("2026-01-01T00:00:00Z"))) == 3
    assert last_query()["offset"] == ["2"]


@resp.activate
def test_iter_resource_updates_stops_on_empty_page(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/updates",
        json={"returned_item_count": 0, "total_item_count": 5, "offset": 0, "items": []},
    )
    assert list(client.iter_resource_updates("2026-01-01T00:00:00Z")) == []


@resp.activate
def test_count_resource_updates(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/updates",
        json={"returned_item_count": 1, "total_item_count": 917, "offset": 0, "items": []},
    )
    assert client.count_resource_updates("2026-01-01T00:00:00Z", resource_code="X") == 917
    assert last_query()["limit"] == ["1"]


@resp.activate
def test_get_resource_and_language_detail(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/resources/R", json={"resource_code": "R"})
    resp.add(
        resp.GET, f"{BASE_URL}/resources/R/fra", json={"resource_code": "R", "language": "fra"}
    )
    assert client.get_resource("R", format="pdf")["resource_code"] == "R"
    assert last_query() == {"format": ["pdf"]}
    assert client.get_resource_language("R", "fra")["language"] == "fra"


@resp.activate
def test_get_resource_files(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/R/eng/files",
        json={"resource_code": "R", "language": "eng", "files": [], "alignments": [], "audio": []},
    )
    client.get_resource_files("R", "eng", book_code="GEN", group="a")
    assert last_query() == {"book_code": ["GEN"], "group": ["a"]}


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------


@resp.activate
def test_get_article(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/AquiferOpenBibleDictionary/eng/articles/3263",
        json=SAMPLE_ARTICLE,
    )
    article = client.get_article(
        "AquiferOpenBibleDictionary", "eng", 3263, content_format="markdown"
    )
    assert article["title"] == "Aaron"
    assert last_query() == {"content_format": ["markdown"]}


@resp.activate
def test_get_articles_include_sequence(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/R/eng/articles",
        json={"articles": [], "license_info": LICENSE_INFO, "pagination": page(1, 0)},
    )
    client.get_articles(
        "R", "eng", include=["content", "localizations"], updated_since="2026-01-01"
    )
    assert last_query() == {
        "include": ["content,localizations"],
        "updated_since": ["2026-01-01"],
    }


@resp.activate
def test_iter_articles_follows_pages(client: AquiferClient) -> None:
    for n in (1, 2, 3):
        resp.add(
            resp.GET,
            f"{BASE_URL}/resources/R/eng/articles",
            json={"articles": [{"content_id": str(n)}], "pagination": page(n, 3, 1)},
        )
    assert [
        a["content_id"] for a in client.iter_articles("R", "eng", content_format="markdown")
    ] == [
        "1",
        "2",
        "3",
    ]
    assert last_query()["per_page"] == ["100"]
    assert last_query()["content_format"] == ["markdown"]


@resp.activate
def test_get_license_info(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/resources/R/fra/articles",
        json={"articles": [], "license_info": LICENSE_INFO, "pagination": page(1, 0)},
    )
    assert client.get_license_info("R", "fra")["adaptation_notice"] == "<p>Adapted.</p>"
    assert last_query() == {"include": ["none"], "per_page": ["1"]}


@resp.activate
def test_article_subresources(client: AquiferClient) -> None:
    base = f"{BASE_URL}/resources/R/eng/articles/9"
    resp.add(resp.GET, f"{base}/associations", json={"content_id": "9"})
    resp.add(resp.GET, f"{base}/available-languages", json={"content_id": "9"})
    resp.add(
        resp.GET, f"{base}/tokens", json={"tokens": [{"token_id": "o1"}], "pagination": page(1, 1)}
    )
    assert client.get_article_associations("R", "eng", "9")["content_id"] == "9"
    assert client.get_article_available_languages("R", "eng", "9")["content_id"] == "9"
    assert client.get_article_tokens("R", "eng", "9", per_page=5)["tokens"][0]["token_id"] == "o1"
    assert [t["token_id"] for t in client.iter_article_tokens("R", "eng", "9")] == ["o1"]


# ---------------------------------------------------------------------------
# Passages
# ---------------------------------------------------------------------------


@resp.activate
def test_get_passage_articles_encodes_ref_and_repeats_params(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/passages/GEN%201%3A1-3/articles",
        json={"articles": [], "pagination": page(1, 0)},
    )
    client.get_passage_articles(
        "GEN 1:1-3",
        resource_type=["Study Notes", "Images, Maps, Videos"],
        order="specificity",
        include_content=True,
    )
    assert "/passages/GEN%201%3A1-3/articles" in resp.calls[0].request.url
    assert last_query() == {
        "resource_type": ["Study Notes", "Images, Maps, Videos"],
        "order": ["specificity"],
        "include_content": ["true"],
    }


@resp.activate
def test_iter_passage_articles(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/passages/JHN%203/articles",
        json={"articles": [{"content_id": "1"}], "pagination": page(1, 1)},
    )
    assert len(list(client.iter_passage_articles("JHN 3", language="fra"))) == 1
    assert last_query()["language"] == ["fra"]


@resp.activate
def test_get_passage_resource_counts(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/passages/GEN%201%3A1/resource-counts",
        json={"ref": "GEN 1:1", "languages": []},
    )
    client.get_passage_resource_counts("GEN 1:1", languages=["eng", "arb"])
    assert last_query() == {"languages": ["eng,arb"]}


@resp.activate
def test_get_passage_tokens(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/passages/GEN%201%3A1/tokens",
        json={"passage": "GEN 1:1", "tokens": [], "alignment": []},
    )
    client.get_passage_tokens("GEN 1:1", "BereanStandardBible", include_alignment=True)
    assert last_query() == {"bible_id": ["BereanStandardBible"], "include": ["alignment"]}
    client.get_passage_tokens("GEN 1:1", "BereanStandardBible")
    assert "include" not in last_query()


# ---------------------------------------------------------------------------
# Bibles
# ---------------------------------------------------------------------------


@resp.activate
def test_get_bibles_and_iter(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/bibles",
        json={"language": "eng", "bibles": [SAMPLE_BIBLE], "pagination": page(1, 1)},
    )
    assert client.get_bibles(language="eng")["bibles"][0]["abbreviation"] == "BSB"
    assert [b["id"] for b in client.iter_bibles(language="eng", has_audio=True)] == [1]


@resp.activate
def test_get_bible_books(client: AquiferClient) -> None:
    resp.add(
        resp.GET,
        f"{BASE_URL}/bibles/books",
        json={"books": [{"book": 1, "usfm_code": "GEN", "name": "Genesis", "osis_id": "Gen"}]},
    )
    assert client.get_bible_books()["books"][0]["usfm_code"] == "GEN"


@resp.activate
def test_get_bible_text_by_ref(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/texts", json={"chapters": []})
    client.get_bible_text(1, "JHN 3", language="fra", should_return_audio_data=True)
    assert last_query() == {
        "ref": ["JHN 3"],
        "language": ["fra"],
        "should_return_audio_data": ["true"],
    }


@resp.activate
def test_get_bible_text_by_book_code(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/bibles/BereanStandardBible/texts", json={"chapters": []})
    client.get_bible_text("BereanStandardBible", book_code="GEN", start_chapter=1, end_chapter=3)
    assert last_query() == {"book_code": ["GEN"], "start_chapter": ["1"], "end_chapter": ["3"]}


def test_get_bible_text_requires_exactly_one_selector(client: AquiferClient) -> None:
    with pytest.raises(ValueError):
        client.get_bible_text(1)
    with pytest.raises(ValueError):
        client.get_bible_text(1, "GEN 1", book_code="GEN")


@resp.activate
def test_get_bible_verses_chunks_and_merges(client: AquiferClient) -> None:
    refs = [f"PSA 1:{i}" for i in range(1, 251)]

    def body(chunk: list[str], missing: list[str]) -> dict:
        return {
            "id": 1,
            "verses": [{"ref": r} for r in chunk],
            "missing": missing,
        }

    resp.add(resp.GET, f"{BASE_URL}/bibles/1/texts", json=body(refs[:200], ["PSA 1:7"]))
    resp.add(resp.GET, f"{BASE_URL}/bibles/1/texts", json=body(refs[200:], ["PSA 1:240"]))
    merged = client.get_bible_verses(1, refs)
    assert len(resp.calls) == 2
    assert len(parse_qs(urlparse(resp.calls[0].request.url).query)["refs"][0].split(",")) == 200
    assert [v["ref"] for v in merged["verses"]] == refs
    assert merged["missing"] == ["PSA 1:7", "PSA 1:240"]


def test_get_bible_verses_rejects_empty(client: AquiferClient) -> None:
    with pytest.raises(ValueError):
        client.get_bible_verses(1, [])


# ---------------------------------------------------------------------------
# ACAI and tokens
# ---------------------------------------------------------------------------


@resp.activate
def test_acai_lists(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/acai/types", json={"types": []})
    resp.add(
        resp.GET,
        f"{BASE_URL}/acai",
        json={"entities": [{"acai_id": "person:Aaron"}], "pagination": page(1, 1)},
    )
    client.get_acai_types()
    client.get_acai_entities(type="person", include_variants=True)
    assert last_query() == {"type": ["person"], "include_variants": ["true"]}
    assert [e["acai_id"] for e in client.iter_acai_entities(type="person")] == ["person:Aaron"]


@resp.activate
def test_acai_entity_id_keeps_colon(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/acai/person:Aaron", json={"acai_id": "person:Aaron"})
    assert client.get_acai_entity("person:Aaron", language="fra")["acai_id"] == "person:Aaron"
    assert last_path() == "/acai/person:Aaron"


@resp.activate
def test_acai_subresources(client: AquiferClient) -> None:
    for sub, key in (
        ("references", "references"),
        ("speeches", "speeches"),
        ("tokens", "tokens"),
        ("articles", "articles"),
    ):
        resp.add(
            resp.GET,
            f"{BASE_URL}/acai/person:Aaron/{sub}",
            json={"acai_id": "person:Aaron", key: [{"x": 1}], "pagination": page(1, 1)},
        )
    assert client.get_acai_references("person:Aaron")["references"] == [{"x": 1}]
    assert client.get_acai_speeches("person:Aaron")["speeches"] == [{"x": 1}]
    assert client.get_acai_tokens("person:Aaron", per_page=10)["tokens"] == [{"x": 1}]
    assert client.get_acai_articles("person:Aaron", min_confidence=0.8)["articles"] == [{"x": 1}]
    assert last_query() == {"min_confidence": ["0.8"]}
    assert len(list(client.iter_acai_references("person:Aaron"))) == 1
    assert len(list(client.iter_acai_speeches("person:Aaron"))) == 1
    assert len(list(client.iter_acai_tokens("person:Aaron"))) == 1
    assert len(list(client.iter_acai_articles("person:Aaron", language="fra"))) == 1


@resp.activate
def test_get_token(client: AquiferClient) -> None:
    resp.add(resp.GET, f"{BASE_URL}/tokens/o01001001003", json={"token_id": "o01001001003"})
    assert client.get_token("o01001001003")["token_id"] == "o01001001003"
