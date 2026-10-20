# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-20

Rewritten for the v2 API (`https://api2.aquifer.bible`). **Breaking:** every method,
parameter and response shape changed; v1 is no longer supported. Existing API keys still work.

### Added
- Methods for every v2 endpoint: languages, resources (catalog, types, search, updates,
  detail, files), articles (detail, bulk, associations, available-languages, tokens),
  passages (articles, resource-counts, tokens with alignment), bibles (catalog, books,
  text, `?refs=` batch), ACAI, and source tokens
- `iter_*` generators that follow pagination, including offset-based `iter_resource_updates`
- `AquiferAPIError` (a `requests.HTTPError`) exposing the parsed error body and `did_you_mean`
- `client.rate_limit` (last `RateLimit-*` headers); deprecation warnings for renamed resource codes
- `RESOURCE_CODE_RENAMES` and `current_resource_code()`
- `AQUIFER_API_BASE_URL` support in `from_env()`

### Changed
- Default base URL is `https://api2.aquifer.bible`; default request timeout is 60 s
- Response models are v2 `snake_case` `TypedDict`s; lists are wrapped with `pagination`
- Retries honor `Retry-After` on 429

### Removed
- All v1 methods (Greek alignment dump, collections, `by-language`, numeric content ids)

## [0.1.0] - 2026-03-23

### Added
- `AquiferClient` with automatic retry (7 attempts, exponential backoff)
- Context manager support (`with AquiferClient(...) as client:`)
- `AquiferClient.from_env()` factory method
- Full typed `TypedDict` models for all API response shapes
- All documented API endpoints: languages, bibles, bible text, Greek alignment,
  resources, resource collections, resource updates
- Undocumented `GET /bibles/{bibleId}/books` endpoint (known to work in practice)
- `bible_books` module: `OT_BOOKS`, `NT_BOOKS`, `APOCRYPHA_BOOKS`, `USFM_BOOK_CODES`,
  and predicate helpers
- `languages` module: `LanguageInfo` dataclass and `LANGUAGES` registry for 24 languages
