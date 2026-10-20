# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Python (>=3.11) client library for the **v2** Aquifer API (`https://api2.aquifer.bible`; v1 keys work). Packaged with Poetry; the importable package is `aquifer` under `src/`. Internal API docs live in `../api/docs` (`api_reference.md` is the contract; `v1_to_v2_migration_guide.md` explains the renamed nouns: v2 *resource* = container, *article* = item). `../../BN-Content/dc-pipeline/src/dc_pipeline/aquifer.py` is a small consumer-side v2 client.

## Commands

```bash
pip install -e ".[dev]"                  # or: poetry install

pytest -m "not integration"              # unit tests (HTTP mocked with `responses`, no key needed)
pytest tests/test_client.py::TestName::test_name   # single test
pytest -m integration                    # live API tests; need AQUIFER_API_KEY (skipped otherwise)

ruff check src tests                     # lint (E, F, I, UP; line length 100)
mypy src                                 # strict mode
```

## Architecture

- `src/aquifer/client.py` — `AquiferClient` is the whole API surface: one `get_*` method per endpoint (returns a single response/page) plus `iter_*` generators built on `_paginate()`. Everything funnels through `_get()`, which sends the `api-key` header, drops `None` params, lowercases bools, records `RateLimit-*` headers, warns on `Deprecation`, and raises `AquiferAPIError` on non-2xx. The urllib3 `Retry` adapter honors `Retry-After`. Python args map 1:1 to the API's snake_case params; comma-list params accept sequences via `_csv()`, while repeatable ones (`resource_type` on passage articles) are passed as lists so requests repeats the key. Path segments go through `_seg()` (refs like `GEN 1:1` must be percent-encoded; ACAI ids keep `:`).
- `src/aquifer/models.py` — response types are `TypedDict`s (plain dicts at runtime, no validation). `resource_type`/`aquifer_type` are plain `str` because the API says they are open sets. Add new endpoint response types here and export them from `__init__.py` (the export list mirrors every name in `models.py`).
- `resource_codes.py` — renamed-resource_code table; `bible_books.py`, `languages.py` — static helpers needing no API call (`languages.py` is a hand-maintained subset; `get_languages()` is authoritative).
- `src/aquifer/__init__.py` — public API; everything users import must be re-exported here.

## Conventions

- Keep the README "API reference" table in sync when adding or changing client methods; keep the v0.1→v0.2 migration table accurate.
- Unit tests share sample payloads and a `client` fixture from `tests/conftest.py`; integration tests are marked `integration` and define their own module-scoped client.
- Pagination: `page`/`per_page` (max 100; `GET /resources` max 500) everywhere except `/resources/updates`, which uses `limit` (max 1000)/`offset`.
- Update `CHANGELOG.md` for user-visible changes.
