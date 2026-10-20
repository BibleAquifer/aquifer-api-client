# aquifer-api-client

Python client for the [Aquifer Bible API v2](https://api2.aquifer.bible). Provides typed access to Bibles, study resources and articles, Greek/Hebrew word alignment, the ACAI entity registry, and more. Version 0.2 targets API v2 only; see [Migrating from v0.1](#migrating-from-v01-api-v1).

The aquifer-api-client hits the Aquifer database (AquiferDB) to access resources granularly through an API. Note that the API used does not directly access resources available on GitHub here, but an upstream database of resources that is used by the [Bible Well mobile app](https://well.bible).

Our longer-term intention is to replace the AquiferDB API with an API and MCP server that provide access to the resources in the BibleAquifer GitHub repositories.

Request an AquiferDB API Key: https://www.aquifer.bible/apiaccess (existing v1 keys work with v2).

Clone and run a demo implementation using `aquifer-api-client`: https://github.com/BibleAquifer/aquifer-api-client-demo

## Formal API Documentation

An interactive explorer is served at https://api2.aquifer.bible/docs and the OpenAPI document at https://api2.aquifer.bible/openapi.json.

This code is a set of helper functions for Python that make accessing API functions a bit easier in the Python environment.

## Installation

(Note: We plan to upload to PyPI but have not yet taken this step.)

```bash
pip install aquifer-api-client
```

## Authentication

You need an Aquifer API key (v1 keys work on v2). Store it in a `.env` file (never commit this to version control):

```
AQUIFER_API_KEY=your-key-here
```

`AquiferClient.from_env()` reads the variable with `os.getenv()`, so any of these work:

- **System environment variable** — set `AQUIFER_API_KEY` in your OS or shell profile
- **Shell export** — `export AQUIFER_API_KEY="your-key-here"` before running your script
- **`.env` file** — load with [`python-dotenv`](https://pypi.org/project/python-dotenv/) at startup:

```python
from dotenv import load_dotenv
load_dotenv()  # reads .env from the current directory
```

- **CI/CD secrets** — inject as an environment variable in your pipeline; no code changes needed

Set `AQUIFER_API_BASE_URL` to point `from_env()` at a different server (e.g. a local dev instance).

## Quickstart

```python
from aquifer import AquiferClient

# From environment variable (recommended)
with AquiferClient.from_env() as client:
    bibles = client.get_bibles(language="eng")["bibles"]
    print(bibles[0]["name"])  # "Berean Standard Bible"

# Explicit key
client = AquiferClient(api_key="your-key")
```

Methods named `get_*` return one response (one page, for paginated endpoints). `iter_*`
methods follow pagination and yield individual items. Responses are plain dicts with the
API's own `snake_case` keys, typed with `TypedDict`s from `aquifer.models`.

## Usage examples

### Terminology

v2 swapped v1's two nouns: a **resource** is a container (the Berean Standard Bible, the
Aquifer Open Bible Dictionary; keyed by `resource_code`) and an **article** is one item in it
(a dictionary entry; keyed by `content_id`, scoped by resource and language).

### Fetch Bible text

```python
with AquiferClient.from_env() as client:
    # By reference (USFM, OSIS or BCV8; whole chapters and books are accepted)
    text = client.get_bible_text("BereanStandardBible", "RUT 1", should_return_audio_data=True)

    # By book and chapter bounds
    gen = client.get_bible_text(1, book_code="GEN", start_chapter=1, end_chapter=3)

    for chapter in text["chapters"]:
        for verse in chapter["verses"]:
            print(f"{chapter['number']}:{verse['number']}  {verse['text']}")

    # A discontiguous list of verses in one call (split automatically past 200 refs)
    batch = client.get_bible_verses("BereanStandardBible", ["GEN 1:1", "JHN 3:16"])
    print(batch["verses"], batch["missing"])
```

### Word alignment (interlinear)

```python
with AquiferClient.from_env() as client:
    body = client.get_passage_tokens("MAT 1:1", "BereanStandardBible", include_alignment=True)
    for record in body["alignment"]:
        if record["translation"]:
            words = " ".join(w["text"] for w in record["translation"]["words"])
            print(words, "→", [s["lemma"] for s in record["source"]])
```

Check `has_alignments` on the Bible first: a Bible with no word tokenization returns a 404.

### Find articles for a passage

```python
with AquiferClient.from_env() as client:
    page = client.get_passage_articles("RUT 2:1", resource_type="Study Notes", per_page=100)
    print(page["pagination"]["total"], "study notes for Ruth 2:1")

    # Every match, following pagination
    for row in client.iter_passage_articles("RUT 2", language="eng"):
        print(row["resource_code"], row["content_id"], row["title"])

    # Counts per language and resource type
    counts = client.get_passage_resource_counts("RUT 2:1", languages=["eng", "fra"])
```

### Search and fetch articles

```python
with AquiferClient.from_env() as client:
    # Title search (not full-text)
    hit = client.search_articles("Aaron", language="eng")["results"][0]

    article = client.get_article(
        hit["resource_code"], hit["language_code"], hit["content_id"], content_format="markdown"
    )
    print(article["title"], article["content"])
    print(client.get_article_associations(hit["resource_code"], "eng", hit["content_id"]))
```

### Mirror a whole resource

```python
with AquiferClient.from_env() as client:
    for article in client.iter_articles(
        "AquiferOpenBibleDictionary", "eng", include="content,localizations",
        content_format="markdown", updated_since="2026-01-01T00:00:00Z",
    ):
        print(article["content_id"], article["title"])
```

### Change feed (sync workflow)

```python
with AquiferClient.from_env() as client:
    if client.count_resource_updates("2026-01-01T00:00:00Z", resource_code="FIATranslationGuide"):
        for item in client.iter_resource_updates(
            "2026-01-01T00:00:00Z", resource_code="FIATranslationGuide", language_code="fra"
        ):
            print(item["update_type"], item["content_id"], item["timestamp"])  # "updated" | "deleted"
```

`start_timestamp` is inclusive. Items carry identifiers only; fetch content with `get_article`.

### ACAI (biblical entities)

```python
with AquiferClient.from_env() as client:
    aaron = client.get_acai_entity("person:Aaron")
    print(aaron["localization"]["preferred_label"], aaron["reference_count"])
    for ref in client.iter_acai_references("person:Aaron"):
        print(ref["ref"])
```

### Errors, retries and rate limits

Non-2xx responses raise `AquiferAPIError` (a `requests.HTTPError` subclass) with the parsed
body in `.detail`; for an unknown `resource_code`, `.did_you_mean` lists suggestions.
Requests retry on 429/5xx, honoring `Retry-After`. `client.rate_limit` holds the last
`RateLimit-*` headers.

Renamed resource codes (e.g. `TyndaleBibleDictionary`) still resolve but log a deprecation
warning; `aquifer.RESOURCE_CODE_RENAMES` and `current_resource_code()` help migrate stored codes.

### Language and Bible helpers

```python
from aquifer import LANGUAGES, is_rtl, NT_BOOKS, book_is_nt

print(LANGUAGES["arb"].name)   # "Arabic"
print(is_rtl("fas"))           # True
print(book_is_nt("REV"))       # True
```

## API reference

| Method | Endpoint |
|---|---|
| `get_languages()` | `GET /languages` |
| `get_resources(...)` / `iter_resources(...)` | `GET /resources` |
| `get_resource_types(group_by=)` | `GET /resources/types` |
| `search_articles(query, ...)` / `iter_search_articles(...)` | `GET /resources/search` |
| `get_resource_updates(start_timestamp, ...)` / `iter_resource_updates(...)` / `count_resource_updates(...)` | `GET /resources/updates` |
| `get_resource(resource_code)` | `GET /resources/{resource_code}` |
| `get_resource_language(resource_code, language)` | `GET /resources/{resource_code}/{language}` |
| `get_resource_files(resource_code, language, ...)` | `GET /resources/{resource_code}/{language}/files` |
| `get_article(resource_code, language, content_id, ...)` | `GET /resources/{rc}/{language}/articles/{content_id}` |
| `get_articles(...)` / `iter_articles(...)` / `get_license_info(...)` | `GET /resources/{rc}/{language}/articles` |
| `get_article_associations(...)` | `.../articles/{content_id}/associations` |
| `get_article_available_languages(...)` | `.../articles/{content_id}/available-languages` |
| `get_article_tokens(...)` / `iter_article_tokens(...)` | `.../articles/{content_id}/tokens` |
| `get_passage_articles(ref, ...)` / `iter_passage_articles(...)` | `GET /passages/{ref}/articles` |
| `get_passage_resource_counts(ref, ...)` | `GET /passages/{ref}/resource-counts` |
| `get_passage_tokens(ref, bible_id, ...)` | `GET /passages/{ref}/tokens` |
| `get_bibles(...)` / `iter_bibles(...)` | `GET /bibles` |
| `get_bible_books()` | `GET /bibles/books` |
| `get_bible_text(bible_id, ref=…)` | `GET /bibles/{bible_id}/texts` |
| `get_bible_verses(bible_id, refs)` | `GET /bibles/{bible_id}/texts?refs=` |
| `get_acai_types()` | `GET /acai/types` |
| `get_acai_entities(...)` / `iter_acai_entities(...)` | `GET /acai` |
| `get_acai_entity(acai_id)` | `GET /acai/{acai_id}` |
| `get_acai_references/speeches/tokens/articles(acai_id, ...)` and `iter_*` | `GET /acai/{acai_id}/{references,speeches,tokens,articles}` |
| `get_token(token_id)` | `GET /tokens/{token_id}` |

## Pagination

- Most list endpoints use `page` / `per_page` (default 50, max 100) and return a `pagination` block.
- `get_resources`: `per_page` up to 500.
- `get_resource_updates`: `limit` (max 1000) / `offset`; use `iter_resource_updates` to walk the feed.
- `iter_*` methods request the maximum page size.

## Migrating from v0.1 (API v1)

This release targets the v2 API and is a clean break. Highlights:

| v0.1 (v1) | v0.2 (v2) |
|---|---|
| `get_all_bibles` | `get_bibles` → `{"bibles": [...], "pagination": ...}` |
| `get_bible_book_text` | `get_bible_text` |
| `get_bible_greek_alignment` | `get_passage_tokens(..., include_alignment=True)` |
| `search_resources` (+ passage filter) | `search_articles` (title search), `get_passage_articles` |
| `get_resource(content_id)` | `get_article(resource_code, language, content_id)` |
| `get_resource_collections` / `get_resource_collection` | `get_resources` / `get_resource` |
| `get_languages_available_resources` | `get_passage_resource_counts` |
| `get_resource_by_language` | removed; fetch the sibling via `get_article_available_languages` |
| camelCase keys, bare-array lists | snake_case keys, wrapped lists with `pagination` |

See the [v1→v2 migration guide](https://github.com/BibleAquifer/api/blob/main/docs/v1_to_v2_migration_guide.md)
for the field-by-field mapping.

## Development

```bash
pip install -e ".[dev]"

# Run unit tests (no API key needed)
pytest -m "not integration"

# Run integration tests against the live API (requires AQUIFER_API_KEY)
pytest -m integration

ruff check src tests && mypy src
```
