"""Aquifer API client — HTTP session, retry logic, and typed v2 API methods."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator, Sequence
from types import TracebackType
from typing import Any, cast
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from aquifer.models import (
    AcaiArticlesResponse,
    AcaiEntitiesResponse,
    AcaiEntity,
    AcaiReferencesResponse,
    AcaiSpeechesResponse,
    AcaiTokensResponse,
    AcaiTypesResponse,
    Article,
    ArticleAssociations,
    ArticleAvailableLanguages,
    ArticlesResponse,
    ArticleTokensResponse,
    BibleBooksResponse,
    BiblesResponse,
    BibleText,
    BibleVerses,
    BulkArticle,
    ContentFormat,
    LanguagesResponse,
    LicenseInfo,
    PassageArticlesResponse,
    PassageResourceCounts,
    PassageTokens,
    ResourceDetail,
    ResourceFiles,
    ResourceLanguageDetail,
    ResourcesResponse,
    ResourceSummary,
    ResourceTypesResponse,
    SearchResponse,
    SearchResult,
    SourceToken,
    UpdateItem,
    UpdatesResponse,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api2.aquifer.bible"

MAX_PER_PAGE = 100  # the API caps ``per_page`` here, except on ``GET /resources``
MAX_RESOURCES_PER_PAGE = 500
MAX_UPDATES_LIMIT = 1000
MAX_BATCH_REFS = 200  # ``?refs=`` limit on ``GET /bibles/{id}/texts``


class AquiferAPIError(requests.HTTPError):
    """A non-2xx response from the API.

    Subclasses :class:`requests.HTTPError`, so existing ``except HTTPError`` handlers
    keep working. ``detail`` is the parsed JSON error body, which on 404s carries
    helpful extras such as ``did_you_mean`` (unknown resource_code) or
    ``available_languages`` (unknown language).
    """

    def __init__(self, response: requests.Response) -> None:
        try:
            body = response.json()
        except ValueError:
            body = None
        self.detail: Any = body
        message = body.get("detail") if isinstance(body, dict) else None
        super().__init__(
            f"{response.status_code} {response.reason} for {response.url}"
            + (f": {message}" if message else ""),
            response=response,
        )

    @property
    def status_code(self) -> int:
        assert self.response is not None
        return self.response.status_code

    @property
    def did_you_mean(self) -> list[str]:
        """Suggested resource codes from a 404 for an unknown ``resource_code``."""
        if isinstance(self.detail, dict):
            return list(self.detail.get("did_you_mean") or [])
        return []


def _csv(value: str | Sequence[str] | None) -> str | None:
    """Join a sequence into the comma-separated form the API expects."""
    if value is None or isinstance(value, str):
        return value
    return ",".join(value)


def _seg(value: str | int) -> str:
    """Percent-encode one URL path segment."""
    return quote(str(value), safe="")


class AquiferClient:
    """HTTP client for the Aquifer v2 API with automatic retry.

    Usage::

        # Explicit key
        client = AquiferClient(api_key="your-key")

        # From environment variable (default: AQUIFER_API_KEY)
        client = AquiferClient.from_env()

        # As a context manager (closes the underlying session on exit)
        with AquiferClient.from_env() as client:
            bibles = client.get_bibles(language="eng")["bibles"]

    Methods named ``get_*`` return one response (a single page, for paginated endpoints);
    ``iter_*`` methods follow pagination and yield individual items.

    After each request ``rate_limit`` holds the ``RateLimit-*`` response headers.
    """

    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: float = 60.0) -> None:
        if not api_key:
            raise ValueError("api_key must be a non-empty string")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit: dict[str, str] = {}
        self._headers = {"api-key": api_key}

        # urllib3 honors ``Retry-After`` on 429/503 by default.
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # -- context manager -------------------------------------------------------

    def __enter__(self) -> AquiferClient:
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

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        clean: dict[str, Any] = {}
        for key, value in (params or {}).items():
            if value is None:
                continue
            clean[key] = str(value).lower() if isinstance(value, bool) else value
        resp = self.session.get(url, headers=self._headers, params=clean, timeout=self.timeout)

        self.rate_limit = {
            name: resp.headers[name]
            for name in ("RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset")
            if name in resp.headers
        }
        if resp.headers.get("Deprecation"):
            logger.warning(
                "%s uses a deprecated resource_code; successor: %s",
                path,
                resp.headers.get("Link", "(none given)"),
            )
        if not resp.ok:
            raise AquiferAPIError(resp)
        return resp.json()

    def _paginate(
        self,
        path: str,
        key: str,
        params: dict[str, Any],
        per_page: int = MAX_PER_PAGE,
    ) -> Iterator[Any]:
        """Yield ``body[key]`` items across every page of a ``page``/``per_page`` endpoint."""
        page = 1
        while True:
            body = self._get(path, {**params, "page": page, "per_page": per_page})
            yield from body[key]
            if not body["pagination"]["has_more"]:
                return
            page += 1

    # -- factory ---------------------------------------------------------------

    @classmethod
    def from_env(
        cls,
        env_var: str = "AQUIFER_API_KEY",
        base_url: str | None = None,
        base_url_env_var: str = "AQUIFER_API_BASE_URL",
    ) -> AquiferClient:
        """Create a client using an API key from an environment variable.

        Args:
            env_var: Name of the environment variable holding the API key.
            base_url: API base URL. Defaults to the ``AQUIFER_API_BASE_URL`` environment
                variable if set (handy for a local dev server), else
                ``https://api2.aquifer.bible``.
            base_url_env_var: Name of the environment variable consulted for the base URL.

        Raises:
            ValueError: If the API key environment variable is not set or is empty.
        """
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(
                f"Environment variable {env_var!r} is not set or empty. "
                "Set it to your Aquifer API key."
            )
        return cls(api_key=api_key, base_url=base_url or os.getenv(base_url_env_var) or BASE_URL)

    # -- Languages -------------------------------------------------------------

    def get_languages(self) -> LanguagesResponse:
        """Return every language the API has content for, with metadata."""
        return cast(LanguagesResponse, self._get("languages"))

    # -- Resources (catalog) ---------------------------------------------------

    def get_resources(
        self,
        *,
        language: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> ResourcesResponse:
        """Return one page of the resource catalog (``per_page`` max 500, default 50)."""
        return cast(
            ResourcesResponse,
            self._get("resources", {"language": language, "page": page, "per_page": per_page}),
        )

    def iter_resources(self, *, language: str | None = None) -> Iterator[ResourceSummary]:
        """Yield every resource in the catalog, following pagination."""
        return self._paginate(
            "resources", "resources", {"language": language}, MAX_RESOURCES_PER_PAGE
        )

    def get_resource_types(self, *, group_by: str | None = None) -> ResourceTypesResponse:
        """Return resources grouped by type.

        Args:
            group_by: ``"resource_type"`` (default, fine-grained) or ``"aquifer_type"``
                (the coarse 5-value category).
        """
        return cast(ResourceTypesResponse, self._get("resources/types", {"group_by": group_by}))

    def search_articles(
        self,
        query: str | None = None,
        *,
        book_code: str | None = None,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
        start_verse: int | None = None,
        end_verse: int | None = None,
        language: str | None = None,
        resource_type: str | None = None,
        aquifer_type: str | None = None,
        resource_code: str | None = None,
        content_order: str | Sequence[str] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> SearchResponse:
        """Title search over articles (not article bodies).

        At least one of ``query``, ``book_code``, ``resource_type``, ``aquifer_type`` or
        ``resource_code`` is required. ``query`` must be at least 3 characters; the last
        term is prefix-matched. ``content_order`` defaults server-side to
        ``alphabetical,monograph``; pass ``"all"`` to include canonical-order resources.
        """
        return cast(
            SearchResponse,
            self._get(
                "resources/search",
                {
                    "query": query,
                    "book_code": book_code,
                    "start_chapter": start_chapter,
                    "end_chapter": end_chapter,
                    "start_verse": start_verse,
                    "end_verse": end_verse,
                    "language": language,
                    "resource_type": resource_type,
                    "aquifer_type": aquifer_type,
                    "resource_code": resource_code,
                    "content_order": _csv(content_order),
                    "page": page,
                    "per_page": per_page,
                },
            ),
        )

    def iter_search_articles(
        self, query: str | None = None, **filters: Any
    ) -> Iterator[SearchResult]:
        """Yield every :meth:`search_articles` hit, following pagination.

        Takes the same filters as :meth:`search_articles` (except ``page``/``per_page``).
        """
        filters.pop("page", None)
        filters.pop("per_page", None)
        if "content_order" in filters:
            filters["content_order"] = _csv(filters["content_order"])
        return self._paginate("resources/search", "results", {"query": query, **filters})

    def get_resource_updates(
        self,
        start_timestamp: str,
        *,
        end_timestamp: str | None = None,
        language_code: str | None = None,
        resource_code: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> UpdatesResponse:
        """Return one page of the change feed, oldest first.

        ``start_timestamp`` is inclusive, ``end_timestamp`` exclusive. ``limit`` is
        clamped to 1–1000 by the server. Items carry identifiers only (and deletions as
        ``update_type == "deleted"``); fetch content with :meth:`get_article`.
        """
        return cast(
            UpdatesResponse,
            self._get(
                "resources/updates",
                {
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                    "language_code": language_code,
                    "resource_code": resource_code,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )

    def iter_resource_updates(
        self,
        start_timestamp: str,
        *,
        end_timestamp: str | None = None,
        language_code: str | None = None,
        resource_code: str | None = None,
    ) -> Iterator[UpdateItem]:
        """Yield every change-feed item since ``start_timestamp``, paging by ``offset``."""
        offset = 0
        while True:
            body = self.get_resource_updates(
                start_timestamp,
                end_timestamp=end_timestamp,
                language_code=language_code,
                resource_code=resource_code,
                limit=MAX_UPDATES_LIMIT,
                offset=offset,
            )
            yield from body["items"]
            offset += body["returned_item_count"]
            if body["returned_item_count"] == 0 or offset >= body["total_item_count"]:
                return

    def count_resource_updates(
        self,
        start_timestamp: str,
        *,
        end_timestamp: str | None = None,
        language_code: str | None = None,
        resource_code: str | None = None,
    ) -> int:
        """Return how many articles changed since ``start_timestamp`` (inclusive).

        A cheap "anything new?" check: fetches a single feed row and reads the total.
        """
        body = self.get_resource_updates(
            start_timestamp,
            end_timestamp=end_timestamp,
            language_code=language_code,
            resource_code=resource_code,
            limit=1,
        )
        return body["total_item_count"]

    def get_resource(self, resource_code: str, *, format: str | None = None) -> ResourceDetail:
        """Return language-agnostic resource detail with the per-language rollup.

        Args:
            resource_code: Resource code; renamed (deprecated) codes still resolve.
            format: Narrow each language's ``download_urls`` to one kind
                (``json``/``md``/``pdf``/``docx``/``alignments``/``all``).
        """
        return cast(
            ResourceDetail, self._get(f"resources/{_seg(resource_code)}", {"format": format})
        )

    def get_resource_language(
        self, resource_code: str, language: str, *, format: str | None = None
    ) -> ResourceLanguageDetail:
        """Return one language's resource detail (``by_book``, release ``download_urls``, …)."""
        return cast(
            ResourceLanguageDetail,
            self._get(f"resources/{_seg(resource_code)}/{_seg(language)}", {"format": format}),
        )

    def get_resource_files(
        self,
        resource_code: str,
        language: str,
        *,
        book_code: str | None = None,
        format: str | None = None,
        group: str | None = None,
    ) -> ResourceFiles:
        """Return the per-file download inventory for a resource in one language."""
        return cast(
            ResourceFiles,
            self._get(
                f"resources/{_seg(resource_code)}/{_seg(language)}/files",
                {"book_code": book_code, "format": format, "group": group},
            ),
        )

    # -- Articles --------------------------------------------------------------

    def get_article(
        self,
        resource_code: str,
        language: str,
        content_id: str | int,
        *,
        content_format: ContentFormat | None = None,
    ) -> Article:
        """Return one article (``content_format``: ``html`` default, ``markdown`` or ``json``)."""
        return cast(
            Article,
            self._get(
                f"resources/{_seg(resource_code)}/{_seg(language)}/articles/{_seg(content_id)}",
                {"content_format": content_format},
            ),
        )

    def get_articles(
        self,
        resource_code: str,
        language: str,
        *,
        include: str | Sequence[str] | None = None,
        content_format: ContentFormat | None = None,
        updated_since: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> ArticlesResponse:
        """Return one page of the bulk article listing.

        Args:
            include: Any of ``content``, ``associations``, ``localizations``, ``acai`` (comma
                string or sequence). Omitted → all four; ``"none"`` → bare metadata.
            content_format: Applies only if ``content`` is included.
            updated_since: ISO timestamp filter on each article's ``updated_at``.
        """
        return cast(
            ArticlesResponse,
            self._get(
                f"resources/{_seg(resource_code)}/{_seg(language)}/articles",
                {
                    "include": _csv(include),
                    "content_format": content_format,
                    "updated_since": updated_since,
                    "page": page,
                    "per_page": per_page,
                },
            ),
        )

    def iter_articles(
        self,
        resource_code: str,
        language: str,
        *,
        include: str | Sequence[str] | None = None,
        content_format: ContentFormat | None = None,
        updated_since: str | None = None,
    ) -> Iterator[BulkArticle]:
        """Yield every article of a resource in one language, following pagination."""
        return self._paginate(
            f"resources/{_seg(resource_code)}/{_seg(language)}/articles",
            "articles",
            {
                "include": _csv(include),
                "content_format": content_format,
                "updated_since": updated_since,
            },
        )

    def get_license_info(self, resource_code: str, language: str) -> LicenseInfo:
        """Return a resource's per-language license, copyright and adaptation notice.

        The language-agnostic :meth:`get_resource` carries only the English license; the
        per-language one rides on the bulk listing.
        """
        body = self.get_articles(resource_code, language, include="none", per_page=1)
        return body["license_info"]

    def get_article_associations(
        self, resource_code: str, language: str, content_id: str | int
    ) -> ArticleAssociations:
        """Return one article's passage associations and cross-references to other articles."""
        return cast(
            ArticleAssociations,
            self._get(
                f"resources/{_seg(resource_code)}/{_seg(language)}/articles/"
                f"{_seg(content_id)}/associations"
            ),
        )

    def get_article_available_languages(
        self, resource_code: str, language: str, content_id: str | int
    ) -> ArticleAvailableLanguages:
        """Return one article's sibling translations in other languages."""
        return cast(
            ArticleAvailableLanguages,
            self._get(
                f"resources/{_seg(resource_code)}/{_seg(language)}/articles/"
                f"{_seg(content_id)}/available-languages"
            ),
        )

    def get_article_tokens(
        self,
        resource_code: str,
        language: str,
        content_id: str | int,
        *,
        page: int | None = None,
        per_page: int | None = None,
    ) -> ArticleTokensResponse:
        """Return the Greek/Hebrew source tokens aligned to a lexicon article.

        A non-lexicon article returns an empty ``tokens`` list rather than an error.
        """
        return cast(
            ArticleTokensResponse,
            self._get(
                f"resources/{_seg(resource_code)}/{_seg(language)}/articles/"
                f"{_seg(content_id)}/tokens",
                {"page": page, "per_page": per_page},
            ),
        )

    def iter_article_tokens(
        self, resource_code: str, language: str, content_id: str | int
    ) -> Iterator[SourceToken]:
        """Yield every source token aligned to a lexicon article, following pagination."""
        return self._paginate(
            f"resources/{_seg(resource_code)}/{_seg(language)}/articles/{_seg(content_id)}/tokens",
            "tokens",
            {},
        )

    # -- Passages --------------------------------------------------------------

    def get_passage_articles(
        self,
        ref: str,
        *,
        language: str | None = None,
        resource_type: str | Sequence[str] | None = None,
        resource_code: str | Sequence[str] | None = None,
        exclude_resource_code: str | Sequence[str] | None = None,
        order: str | None = None,
        include_content: bool | None = None,
        content_format: ContentFormat | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PassageArticlesResponse:
        """Return one page of articles whose passage associations overlap ``ref``.

        ``ref`` may be BCV8 (``01001001``), USFM (``GEN 1:1``), OSIS (``Gen.1.1``), a range of
        any of these, or a whole chapter/book (``JHN 3``, ``GEN``). Bible verse rows are
        included unless you filter them out with ``resource_type``. A sequence for
        ``resource_type`` is sent as repeated parameters (type names can contain commas).
        ``order`` is ``"reference"`` (default) or ``"specificity"``.
        """
        return cast(
            PassageArticlesResponse,
            self._get(
                f"passages/{_seg(ref)}/articles",
                {
                    "language": language,
                    "resource_type": resource_type,
                    "resource_code": resource_code,
                    "exclude_resource_code": exclude_resource_code,
                    "order": order,
                    "include_content": include_content,
                    "content_format": content_format,
                    "page": page,
                    "per_page": per_page,
                },
            ),
        )

    def iter_passage_articles(self, ref: str, **filters: Any) -> Iterator[Any]:
        """Yield every :meth:`get_passage_articles` row, following pagination.

        Takes the same filters as :meth:`get_passage_articles` (except ``page``/``per_page``).
        """
        filters.pop("page", None)
        filters.pop("per_page", None)
        return self._paginate(f"passages/{_seg(ref)}/articles", "articles", filters)

    def get_passage_resource_counts(
        self, ref: str, *, languages: str | Sequence[str] | None = None
    ) -> PassageResourceCounts:
        """Return per-language article counts for ``ref``, grouped by resource type.

        ``languages`` omitted → every language. Bible verse rows are not counted.
        """
        return cast(
            PassageResourceCounts,
            self._get(f"passages/{_seg(ref)}/resource-counts", {"languages": _csv(languages)}),
        )

    def get_passage_tokens(
        self,
        ref: str,
        bible_id: str,
        *,
        language: str | None = None,
        include_alignment: bool = False,
    ) -> PassageTokens:
        """Return the translation-token stream for a passage within one book.

        Args:
            ref: Verse or verse range (no whole chapters/books), within a single book.
            bible_id: A Bible's ``resource_code``.
            include_alignment: Also return ``alignment[]`` — the interlinear view, with
                source-text morphology, lexicon articles and ACAI mentions per record.

        Raises:
            AquiferAPIError: 404 with ``{"tokenized": false}`` if the Bible has no word
                tokenization; check ``has_alignments`` on the Bible first.
        """
        return cast(
            PassageTokens,
            self._get(
                f"passages/{_seg(ref)}/tokens",
                {
                    "bible_id": bible_id,
                    "language": language,
                    "include": "alignment" if include_alignment else None,
                },
            ),
        )

    # -- Bibles ----------------------------------------------------------------

    def get_bibles(
        self,
        *,
        language: str | None = None,
        has_audio: bool | None = None,
        has_alignments: bool | None = None,
        is_language_default: bool | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> BiblesResponse:
        """Return one page of the Bible catalog."""
        return cast(
            BiblesResponse,
            self._get(
                "bibles",
                {
                    "language": language,
                    "has_audio": has_audio,
                    "has_alignments": has_alignments,
                    "is_language_default": is_language_default,
                    "page": page,
                    "per_page": per_page,
                },
            ),
        )

    def iter_bibles(self, **filters: Any) -> Iterator[ResourceSummary]:
        """Yield every Bible matching the :meth:`get_bibles` filters, following pagination."""
        filters.pop("page", None)
        filters.pop("per_page", None)
        return self._paginate("bibles", "bibles", filters)

    def get_bible_books(self) -> BibleBooksResponse:
        """Return the 66 canonical books (number, USFM code, name, OSIS id)."""
        return cast(BibleBooksResponse, self._get("bibles/books"))

    def get_bible_text(
        self,
        bible_id: str | int,
        ref: str | None = None,
        *,
        book_code: str | None = None,
        start_chapter: int | None = None,
        start_verse: int | None = None,
        end_chapter: int | None = None,
        end_verse: int | None = None,
        language: str | None = None,
        should_return_audio_data: bool | None = None,
    ) -> BibleText:
        """Return Bible text as nested ``chapters[] → verses[]``.

        Give either ``ref`` (USFM/OSIS/BCV8; whole chapters and books accepted, one book
        maximum) or ``book_code`` with optional chapter/verse bounds (omitted end = rest of
        the book).

        Args:
            bible_id: Numeric Bible id or ``resource_code``.
            language: Defaults to ``eng`` server-side.
        """
        if ref is None and book_code is None:
            raise ValueError("provide either ref or book_code")
        if ref is not None and book_code is not None:
            raise ValueError("ref and book_code are mutually exclusive")
        return cast(
            BibleText,
            self._get(
                f"bibles/{_seg(bible_id)}/texts",
                {
                    "ref": ref,
                    "book_code": book_code,
                    "start_chapter": start_chapter,
                    "start_verse": start_verse,
                    "end_chapter": end_chapter,
                    "end_verse": end_verse,
                    "language": language,
                    "should_return_audio_data": should_return_audio_data,
                },
            ),
        )

    def get_bible_verses(
        self,
        bible_id: str | int,
        refs: Sequence[str],
        *,
        language: str | None = None,
        should_return_audio_data: bool | None = None,
    ) -> BibleVerses:
        """Fetch a discontiguous list of verses in one call (``?refs=`` batch mode).

        Refs may be in any notation and need not share a book. The server accepts 200 per
        request; longer lists are split transparently and merged, preserving request order.
        Refs the Bible has no verse for are listed in ``missing``.
        """
        if not refs:
            raise ValueError("refs must not be empty")
        merged: BibleVerses | None = None
        for start in range(0, len(refs), MAX_BATCH_REFS):
            chunk = refs[start : start + MAX_BATCH_REFS]
            body = cast(
                BibleVerses,
                self._get(
                    f"bibles/{_seg(bible_id)}/texts",
                    {
                        "refs": ",".join(chunk),
                        "language": language,
                        "should_return_audio_data": should_return_audio_data,
                    },
                ),
            )
            if merged is None:
                merged = body
            else:
                merged["verses"].extend(body["verses"])
                merged["missing"].extend(body["missing"])
        assert merged is not None
        return merged

    # -- ACAI (biblical-entity registry) ---------------------------------------

    def get_acai_types(self) -> AcaiTypesResponse:
        """Return per-category entity counts."""
        return cast(AcaiTypesResponse, self._get("acai/types"))

    def get_acai_entities(
        self,
        *,
        type: str | None = None,
        language: str | None = None,
        include_variants: bool | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> AcaiEntitiesResponse:
        """Return one page of ACAI entities (primary forms only unless ``include_variants``)."""
        return cast(
            AcaiEntitiesResponse,
            self._get(
                "acai",
                {
                    "type": type,
                    "language": language,
                    "include_variants": include_variants,
                    "page": page,
                    "per_page": per_page,
                },
            ),
        )

    def iter_acai_entities(self, **filters: Any) -> Iterator[Any]:
        """Yield every entity matching the :meth:`get_acai_entities` filters."""
        filters.pop("page", None)
        filters.pop("per_page", None)
        return self._paginate("acai", "entities", filters)

    def get_acai_entity(self, acai_id: str, *, language: str | None = None) -> AcaiEntity:
        """Return entity detail. ``acai_id`` is an exact id such as ``"person:Aaron"``."""
        return cast(
            AcaiEntity, self._get(f"acai/{quote(acai_id, safe=':')}", {"language": language})
        )

    def get_acai_references(
        self, acai_id: str, *, page: int | None = None, per_page: int | None = None
    ) -> AcaiReferencesResponse:
        """Return one page of the entity's Scripture references (BCV8)."""
        return cast(
            AcaiReferencesResponse,
            self._get(
                f"acai/{quote(acai_id, safe=':')}/references",
                {"page": page, "per_page": per_page},
            ),
        )

    def iter_acai_references(self, acai_id: str) -> Iterator[Any]:
        """Yield every Scripture reference of the entity, following pagination."""
        return self._paginate(f"acai/{quote(acai_id, safe=':')}/references", "references", {})

    def get_acai_speeches(
        self, acai_id: str, *, page: int | None = None, per_page: int | None = None
    ) -> AcaiSpeechesResponse:
        """Return one page of speech/quote token spans attributed to the entity."""
        return cast(
            AcaiSpeechesResponse,
            self._get(
                f"acai/{quote(acai_id, safe=':')}/speeches", {"page": page, "per_page": per_page}
            ),
        )

    def iter_acai_speeches(self, acai_id: str) -> Iterator[Any]:
        """Yield every speech span of the entity, following pagination."""
        return self._paginate(f"acai/{quote(acai_id, safe=':')}/speeches", "speeches", {})

    def get_acai_tokens(
        self, acai_id: str, *, page: int | None = None, per_page: int | None = None
    ) -> AcaiTokensResponse:
        """Return one page of word-level mentions of the entity in the source text."""
        return cast(
            AcaiTokensResponse,
            self._get(
                f"acai/{quote(acai_id, safe=':')}/tokens", {"page": page, "per_page": per_page}
            ),
        )

    def iter_acai_tokens(self, acai_id: str) -> Iterator[Any]:
        """Yield every source-text mention of the entity (can be 100k+; consume lazily)."""
        return self._paginate(f"acai/{quote(acai_id, safe=':')}/tokens", "tokens", {})

    def get_acai_articles(
        self,
        acai_id: str,
        *,
        language: str | None = None,
        min_confidence: float | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> AcaiArticlesResponse:
        """Return one page of articles (one language) tagged with the entity.

        Ordered by confidence, descending; ``min_confidence`` (0.0–1.0) drops weaker links.
        """
        return cast(
            AcaiArticlesResponse,
            self._get(
                f"acai/{quote(acai_id, safe=':')}/articles",
                {
                    "language": language,
                    "min_confidence": min_confidence,
                    "page": page,
                    "per_page": per_page,
                },
            ),
        )

    def iter_acai_articles(
        self,
        acai_id: str,
        *,
        language: str | None = None,
        min_confidence: float | None = None,
    ) -> Iterator[Any]:
        """Yield every article tagged with the entity, following pagination."""
        return self._paginate(
            f"acai/{quote(acai_id, safe=':')}/articles",
            "articles",
            {"language": language, "min_confidence": min_confidence},
        )

    # -- Tokens ----------------------------------------------------------------

    def get_token(self, token_id: str) -> SourceToken:
        """Resolve a Greek/Hebrew source-text token id (bare or ``o``/``n``-prefixed)."""
        return cast(SourceToken, self._get(f"tokens/{_seg(token_id)}"))
