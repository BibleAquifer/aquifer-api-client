# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
