"""Aquifer API client — HTTP session, retry logic, and typed API methods."""

from __future__ import annotations

import json
import logging
import os
from types import TracebackType
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from aquifer.models import (
    Associations,
    Bible,
    BibleBook,
    BibleBookText,
    ContentTextType,
    GreekAlignment,
    Language,
    LanguageAvailableResources,
    Resource,
    ResourceAvailableLanguage,
    ResourceCollectionDetail,
    ResourceCollectionSummary,
    ResourceSearchResult,
    ResourceType,
    ResourceTypeGroup,
    ResourceUpdatesResult,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api.aquifer.bible"


class AquiferClient:
    """HTTP client for the Aquifer API with automatic retry.

    Usage::

        # Explicit key
        client = AquiferClient(api_key="your-key")

        # From environment variable (default: AQUIFER_API_KEY)
        client = AquiferClient.from_env()

        # As a context manager (closes the underlying session on exit)
        with AquiferClient.from_env() as client:
            bibles = client.get_all_bibles()
    """

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        if not api_key:
            raise ValueError("api_key must be a non-empty string")
        self.base_url = base_url.rstrip("/")
        self._headers = {"api-key": api_key}

        retry_strategy = Retry(
            total=7,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # -- context manager -------------------------------------------------------

    def __enter__(self) -> "AquiferClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    # -- internal --------------------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None, timeout: int = 10) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.get(url, headers=self._headers, params=params, timeout=timeout)
        resp.raise_for_status()
        return json.loads(resp.text)

    # -- factory ---------------------------------------------------------------

    @classmethod
    def from_env(cls, env_var: str = "AQUIFER_API_KEY", base_url: str = BASE_URL) -> "AquiferClient":
        """Create a client using an API key from an environment variable.

        Args:
            env_var: Name of the environment variable holding the API key.
            base_url: API base URL (defaults to ``https://api.aquifer.bible``).

        Raises:
            ValueError: If the environment variable is not set or is empty.
        """
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(
                f"Environment variable {env_var!r} is not set or empty. "
                "Set it to your Aquifer API key."
            )
        return cls(api_key=api_key, base_url=base_url)

    # -- Languages -------------------------------------------------------------

    def get_languages(self) -> list[Language]:
        """Return all languages available in the Aquifer."""
        return self._get("languages")

    def get_language_map(self) -> tuple[dict[int, str], list[Language]]:
        """Return ``(id → code, language list)`` — convenience for common lookup patterns."""
        languages = self.get_languages()
        return {lang["id"]: lang["code"] for lang in languages}, languages

    def get_languages_available_resources(
        self,
        book_code: str,
        *,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
        start_verse: int | None = None,
        end_verse: int | None = None,
        language_codes: list[str] | None = None,
    ) -> list[LanguageAvailableResources]:
        """Return resource counts per language for a given Bible passage.

        Args:
            book_code: USFM book code (e.g. ``"MAT"``).
            start_chapter: First chapter of the passage range.
            end_chapter: Last chapter of the passage range.
            start_verse: First verse of the passage range.
            end_verse: Last verse of the passage range.
            language_codes: ISO 639-3 codes to filter by.
        """
        params: dict[str, Any] = {"bookCode": book_code}
        if start_chapter is not None:
            params["startChapter"] = start_chapter
        if end_chapter is not None:
            params["endChapter"] = end_chapter
        if start_verse is not None:
            params["startVerse"] = start_verse
        if end_verse is not None:
            params["endVerse"] = end_verse
        if language_codes:
            params["languageCodes"] = language_codes
        return self._get("languages/available-resources", params=params)

    # -- Bibles ----------------------------------------------------------------

    def get_all_bibles(
        self,
        *,
        language_id: int | None = None,
        language_code: str | None = None,
        is_language_default: bool | None = None,
        has_audio: bool | None = None,
        has_greek_alignment: bool | None = None,
    ) -> list[Bible]:
        """Return available Bibles, with optional filters.

        Args:
            language_id: Filter by language ID.
            language_code: Filter by ISO 639-3 code (e.g. ``"eng"``).
            is_language_default: If True, return only the default Bible per language.
            has_audio: If True, return only Bibles with audio.
            has_greek_alignment: If True, return only Bibles with Greek alignment data.
        """
        params: dict[str, Any] = {}
        if language_id is not None:
            params["languageId"] = language_id
        if language_code is not None:
            params["languageCode"] = language_code
        if is_language_default is not None:
            params["isLanguageDefault"] = is_language_default
        if has_audio is not None:
            params["hasAudio"] = has_audio
        if has_greek_alignment is not None:
            params["hasGreekAlignment"] = has_greek_alignment
        return self._get("bibles", params=params or None)

    def get_all_bible_books(self) -> list[BibleBook]:
        """Return the global list of Bible books (code + name pairs)."""
        return self._get("bibles/books")

    def get_bible_books(self, bible_id: int) -> list[BibleBook]:
        """Return the book list for a specific Bible.

        .. note::
            This endpoint is not documented in the public Aquifer API spec
            but is known to work in practice.
        """
        return self._get(f"bibles/{bible_id}/books")

    def get_bible_book_text(
        self,
        bible_id: int,
        book_code: str,
        *,
        start_chapter: int | None = None,
        start_verse: int | None = None,
        end_chapter: int | None = None,
        end_verse: int | None = None,
        audio: bool = False,
    ) -> BibleBookText:
        """Return Bible text for a book or passage range.

        Omitting all range parameters returns the entire book.

        Args:
            bible_id: Aquifer Bible ID.
            book_code: USFM book code (e.g. ``"MAT"``).
            start_chapter: First chapter (default: 1).
            start_verse: First verse (default: 0).
            end_chapter: Last chapter (default: 999).
            end_verse: Last verse (default: 999).
            audio: If True, include chapter audio URLs and verse timestamps.
        """
        params: dict[str, Any] = {"bookCode": book_code}
        if start_chapter is not None:
            params["startChapter"] = start_chapter
        if start_verse is not None:
            params["startVerse"] = start_verse
        if end_chapter is not None:
            params["endChapter"] = end_chapter
        if end_verse is not None:
            params["endVerse"] = end_verse
        if audio:
            params["shouldReturnAudioData"] = True
        return self._get(f"bibles/{bible_id}/texts", params=params, timeout=60)

    def get_bible_greek_alignment(
        self,
        bible_id: int,
        book_code: str,
        *,
        start_chapter: int | None = None,
        start_verse: int | None = None,
        start_word: int | None = None,
        end_chapter: int | None = None,
        end_verse: int | None = None,
        end_word: int | None = None,
        sense_data: bool = False,
    ) -> GreekAlignment:
        """Return Greek alignment data for a Bible passage.

        Only available for NT books in Bibles where ``hasGreekAlignment`` is True.

        Args:
            bible_id: Aquifer Bible ID.
            book_code: USFM NT book code (e.g. ``"MAT"``).
            start_chapter: First chapter (default: 1).
            start_verse: First verse (default: 0).
            start_word: First word within the verse (default: 1).
            end_chapter: Last chapter (default: 999).
            end_verse: Last verse (default: 999).
            end_word: Last word within the verse (default: 999).
            sense_data: If True, include gloss and definition data on each Greek word.
        """
        params: dict[str, Any] = {"bookCode": book_code}
        if start_chapter is not None:
            params["startChapter"] = start_chapter
        if start_verse is not None:
            params["startVerse"] = start_verse
        if start_word is not None:
            params["startWord"] = start_word
        if end_chapter is not None:
            params["endChapter"] = end_chapter
        if end_verse is not None:
            params["endVerse"] = end_verse
        if end_word is not None:
            params["endWord"] = end_word
        if sense_data:
            params["shouldReturnSenseData"] = True
        return self._get(f"bibles/{bible_id}/alignments/greek", params=params, timeout=60)

    # -- Resource types & collections ------------------------------------------

    def get_resource_types(self) -> list[ResourceTypeGroup]:
        """Return all resource types and their collections with license info."""
        return self._get("resources/types")

    def get_resource_collections(
        self,
        *,
        resource_type: ResourceType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResourceCollectionSummary]:
        """Return the list of resource collections.

        Args:
            resource_type: Filter to a specific resource type.
            limit: Max results per call (default: 100).
            offset: Pagination offset (default: 0).
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if resource_type is not None:
            params["resourceType"] = resource_type
        return self._get("resources/collections", params=params)

    def get_resource_collection(
        self,
        code: str,
        *,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
    ) -> ResourceCollectionDetail:
        """Return a resource collection with language availability and license info.

        Args:
            code: Collection code (e.g. ``"BiblicaStudyNotes"``).
            language_codes: Filter available languages by ISO 639-3 codes.
            language_ids: Filter available languages by IDs.
        """
        params: dict[str, Any] = {}
        if language_codes:
            params["languageCodes"] = language_codes
        if language_ids:
            params["languageIds"] = language_ids
        return self._get(f"resources/collections/{code}", params=params or None)

    # -- Resources -------------------------------------------------------------

    def search_resources(
        self,
        *,
        query: str | None = None,
        book_code: str | None = None,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
        start_verse: int | None = None,
        end_verse: int | None = None,
        language_id: int | None = None,
        language_code: str | None = None,
        resource_type: ResourceType | None = None,
        resource_collection_code: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> ResourceSearchResult:
        """Search resources by passage, keyword, type, or collection.

        The API returns at most 100 items per call. Use ``offset`` to paginate
        through ``totalItemCount`` results.

        Args:
            query: Keyword search (minimum 3 characters).
            book_code: USFM book code to filter by passage.
            start_chapter: Start of chapter range.
            end_chapter: End of chapter range.
            start_verse: Start of verse range.
            end_verse: End of verse range.
            language_id: Filter by language ID.
            language_code: Filter by ISO 639-3 code (e.g. ``"eng"``).
            resource_type: Filter by resource type.
            resource_collection_code: Filter by collection code.
            limit: Items per call (default: 10, max: 100).
            offset: Pagination offset (default: 0).
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if query is not None:
            params["query"] = query
        if book_code is not None:
            params["bookCode"] = book_code
        if start_chapter is not None:
            params["startChapter"] = start_chapter
        if end_chapter is not None:
            params["endChapter"] = end_chapter
        if start_verse is not None:
            params["startVerse"] = start_verse
        if end_verse is not None:
            params["endVerse"] = end_verse
        if language_id is not None:
            params["languageId"] = language_id
        if language_code is not None:
            params["languageCode"] = language_code
        if resource_type is not None:
            params["resourceType"] = resource_type
        if resource_collection_code is not None:
            params["resourceCollectionCode"] = resource_collection_code
        return self._get("resources/search", params=params)

    def get_resource(
        self,
        content_id: int,
        *,
        text_type: ContentTextType = "Html",
    ) -> Resource:
        """Return full content for a single resource.

        Args:
            content_id: Resource content ID.
            text_type: Format for the ``content`` field (default: ``"Html"``).
        """
        return self._get(f"resources/{content_id}", params={"contentTextType": text_type})

    def get_resource_by_language(
        self,
        content_id: int,
        language_code: str,
        *,
        text_type: ContentTextType = "Html",
    ) -> Resource:
        """Return a resource in a specific language version.

        Raises a 404 ``HTTPError`` if no version exists for that language.

        Args:
            content_id: Resource content ID.
            language_code: ISO 639-3 code of the desired language.
            text_type: Format for the ``content`` field (default: ``"Html"``).
        """
        return self._get(
            f"resources/{content_id}/by-language/{language_code}",
            params={"contentTextType": text_type},
        )

    def get_resource_available_languages(self, content_id: int) -> list[ResourceAvailableLanguage]:
        """Return the languages a resource is available in.

        Args:
            content_id: Resource content ID.
        """
        return self._get(f"resources/{content_id}/available-languages")

    def get_resource_associations(self, content_id: int) -> Associations:
        """Return passage and resource associations for a resource.

        Args:
            content_id: Resource content ID.
        """
        return self._get(f"resources/{content_id}/associations")

    def get_resource_updates(
        self,
        *,
        start_timestamp: str | None = None,
        end_timestamp: str | None = None,
        language_id: int | None = None,
        language_code: str | None = None,
        resource_collection_code: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> ResourceUpdatesResult:
        """Return resources that are new or updated within a time window.

        The API returns at most 1000 items per call. Use ``offset`` to paginate.

        Args:
            start_timestamp: ISO 8601 datetime string for the start of the window.
            end_timestamp: ISO 8601 datetime string for the end of the window
                (defaults to the current UTC time if omitted).
            language_id: Filter by language ID.
            language_code: Filter by ISO 639-3 code.
            resource_collection_code: Filter by collection code.
            limit: Items per call (default: 1000, max: 1000).
            offset: Pagination offset (default: 0).
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if start_timestamp is not None:
            params["startTimestamp"] = start_timestamp
        if end_timestamp is not None:
            params["endTimestamp"] = end_timestamp
        if language_id is not None:
            params["languageId"] = language_id
        if language_code is not None:
            params["languageCode"] = language_code
        if resource_collection_code is not None:
            params["resourceCollectionCode"] = resource_collection_code
        return self._get("resources/updates", params=params)
