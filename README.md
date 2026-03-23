# aquifer-api-client

Python client for the [Aquifer Bible API](https://api.aquifer.bible). Provides typed access to Bibles, resources, Greek alignment data, and more.

## Formal API Documentation

Documentation of the AquiferAPI is available at: https://api.aquifer.bible/docs/index.html?url=/swagger/v1/swagger.json

This code is a set of helper functions for Python that make accessing API functions a bit easier in the Python environment.

## Installation

(Note: We plan to upload to PyPI but have not yet taken this step.)

```bash
pip install aquifer-api-client
```

## Authentication

You need an Aquifer API key. Store it in a `.env` file (never commit this to version control):

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

## Quickstart

```python
from aquifer import AquiferClient

# From environment variable (recommended)
with AquiferClient.from_env() as client:
    bibles = client.get_all_bibles(language_code="eng")
    print(bibles[0]["name"])  # "Berean Standard Bible"

# Explicit key
client = AquiferClient(api_key="your-key")
```

## Usage examples

### Fetch Bible text

```python
with AquiferClient.from_env() as client:
    # Whole book
    text = client.get_bible_book_text(1, "RUT", audio=True)

    # Passage range
    passage = client.get_bible_book_text(1, "GEN", start_chapter=1, end_chapter=3)

    for chapter in text["chapters"]:
        for verse in chapter["verses"]:
            print(f"{chapter['number']}:{verse['number']}  {verse['text']}")
```

### Greek alignment

```python
with AquiferClient.from_env() as client:
    alignment = client.get_bible_greek_alignment(1, "MAT", sense_data=True)
    for chapter in alignment["chapters"]:
        for verse in chapter["verses"]:
            for word in verse["words"]:
                for gw in word["greekWords"]:
                    print(word["word"], "→", gw["lemma"], gw["strongsNumber"])
```

### Search resources by passage

```python
with AquiferClient.from_env() as client:
    result = client.search_resources(
        book_code="RUT",
        start_chapter=2, end_chapter=2,
        start_verse=1, end_verse=1,
        language_code="eng",
        limit=100,
    )
    print(f"{result['totalItemCount']} resources for Ruth 2:1")

    # Paginate through all results
    all_items = []
    offset = 0
    while offset < result["totalItemCount"]:
        page = client.search_resources(
            book_code="RUT", language_code="eng", limit=100, offset=offset
        )
        all_items.extend(page["items"])
        offset += len(page["items"])
```

### Fetch a resource

```python
with AquiferClient.from_env() as client:
    resource = client.get_resource(content_id=12345, text_type="Html")
    print(resource["name"])
    print(resource["content"])  # HTML string

    # In a specific language
    fra_resource = client.get_resource_by_language(12345, "fra")
```

### Resource updates (sync workflow)

```python
with AquiferClient.from_env() as client:
    updates = client.get_resource_updates(
        start_timestamp="2026-01-01T00:00:00Z",
        resource_collection_code="AquiferOpenBibleDictionary",
    )
    for item in updates["items"]:
        print(item["updateType"], item["resourceId"], item["languageCode"])
```

### Language and Bible helpers

```python
from aquifer import LANGUAGES, is_rtl, NT_BOOKS, book_is_nt

print(LANGUAGES["arb"].name)   # "Arabic"
print(is_rtl("fas"))           # True
print(book_is_nt("REV"))       # True
print(book_is_nt("GEN"))       # False
```

## API reference

| Method | Endpoint |
|---|---|
| `get_languages()` | `GET /languages` |
| `get_language_map()` | `GET /languages` (convenience) |
| `get_languages_available_resources(book_code, ...)` | `GET /languages/available-resources` |
| `get_all_bibles(...)` | `GET /bibles` |
| `get_all_bible_books()` | `GET /bibles/books` |
| `get_bible_books(bible_id)` | `GET /bibles/{bibleId}/books` ¹ |
| `get_bible_book_text(bible_id, book_code, ...)` | `GET /bibles/{bibleId}/texts` |
| `get_bible_greek_alignment(bible_id, book_code, ...)` | `GET /bibles/{bibleId}/alignments/greek` |
| `get_resource_types()` | `GET /resources/types` |
| `get_resource_collections(...)` | `GET /resources/collections` |
| `get_resource_collection(code, ...)` | `GET /resources/collections/{code}` |
| `search_resources(...)` | `GET /resources/search` |
| `get_resource(content_id, ...)` | `GET /resources/{contentId}` |
| `get_resource_by_language(content_id, language_code, ...)` | `GET /resources/{contentId}/by-language/{languageCode}` |
| `get_resource_available_languages(content_id)` | `GET /resources/{contentId}/available-languages` |
| `get_resource_associations(content_id)` | `GET /resources/{contentId}/associations` |
| `get_resource_updates(...)` | `GET /resources/updates` |

¹ Undocumented endpoint, known to work in practice.

## Pagination

- `search_resources`: max 100 items per call, use `offset` to paginate through `totalItemCount`
- `get_resource_updates`: max 1000 items per call, use `offset` to paginate

## Development

```bash
pip install -e ".[dev]"

# Run unit tests (no API key needed)
pytest -m "not integration"

# Run integration tests (requires AQUIFER_API_KEY)
pytest -m integration
```
