"""Typed response models for the Aquifer v2 API.

All models are TypedDict — they are plain dicts at runtime with no parsing
overhead. Field names are the API's own ``snake_case``. Fields marked
NotRequired may be absent from the response; fields typed ``X | None`` are
always present but may be null.
"""

from typing import Any, Literal, NotRequired, TypedDict

# ---------------------------------------------------------------------------
# Literal enums
#
# ``resource_type`` and ``aquifer_type`` are deliberately plain ``str`` in the
# models below: the API says neither is a closed set (new values appear as
# resources are published).
# ---------------------------------------------------------------------------

ContentFormat = Literal["html", "markdown", "json"]
ContentOrder = Literal["canonical", "alphabetical", "monograph"]
ReviewLevel = Literal["None", "Community", "Professional", "Ai"]
MediaType = Literal["None", "Text", "Audio", "Video", "Image"]
UpdateType = Literal["updated", "deleted"]
AlignmentStatus = Literal["aligned", "non_equivalent", "unaligned", "punctuation"]
LocalizationBand = Literal[
    "Initial", "Early", "Developing", "Substantial", "Near Completion", "Complete"
]
LinkType = Literal["explicit", "pronominal", "subject"]

# ---------------------------------------------------------------------------
# Shared structures
# ---------------------------------------------------------------------------


class Pagination(TypedDict):
    page: int
    per_page: int
    total: int
    has_more: bool


class CopyrightHolder(TypedDict):
    name: str
    url: str


class Copyright(TypedDict):
    dates: str | None
    holder: CopyrightHolder
    statement: NotRequired[str | None]  # optional HTML attribution statement


class LicenseEntry(TypedDict):
    eng: dict[str, str]  # {"name": "...", "url": "..."}


class LicenseInfo(TypedDict):
    title: str
    copyright: Copyright
    licenses: list[dict[str, dict[str, str]]]  # [{"eng": {"name": ..., "url": ...}}]
    show_adaptation_notice_for_english: bool
    show_adaptation_notice_for_non_english: bool
    adaptation_notice: str | None  # HTML; serve it when the matching flag is true


class Localization(TypedDict):
    percent: float
    band: LocalizationBand
    reference_language: NotRequired[str]  # full block only (scoped resource detail)
    computed_at: NotRequired[str]


class DownloadUrl(TypedDict):
    url: str
    size_bytes: int


# {kind: [DownloadUrl]} — ``all`` is the combined archive; others are per format.
DownloadUrls = dict[str, list[DownloadUrl]]

# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------


class Language(TypedDict):
    language: str  # ISO 639-3
    resource_count: int
    name: str | None
    localized_name: str | None
    iso639_1: str | None
    is_rtl: bool | None
    word_locale: str | None
    id: int | None


class LanguagesResponse(TypedDict):
    languages: list[Language]


# ---------------------------------------------------------------------------
# Resources (catalog)
# ---------------------------------------------------------------------------


class ResourceSummary(TypedDict):
    resource_code: str
    abbreviation: str | None
    name: str
    display_name: str
    resource_type: str
    aquifer_type: str
    content_type: str  # "Html" | "Json"
    content_order: ContentOrder | None
    version: str | None
    language_code: str
    has_audio: bool
    has_alignments: bool
    license_info: LicenseInfo
    localization: Localization | None
    id: NotRequired[int]  # Bibles only
    is_language_default: NotRequired[bool]  # Bibles only


class ResourcesResponse(TypedDict):
    language: str | None
    resources: list[ResourceSummary]
    pagination: Pagination


class ResourceTypeEntry(TypedDict):
    resource_code: str
    name: str
    display_name: str
    resource_type: str
    aquifer_type: str
    content_type: str
    license_info: LicenseInfo


class ResourceTypeGroup(TypedDict):
    type: str
    resource_count: int
    resources: list[ResourceTypeEntry]


class ResourceTypesResponse(TypedDict):
    group_by: str
    types: list[ResourceTypeGroup]


class ResourceAvailableLanguage(TypedDict):
    language: str
    id: int | None
    display_name: str
    article_count: int
    formats: list[str]
    download_urls: DownloadUrls | None
    localization: NotRequired[Localization]


class ResourceDetail(TypedDict):
    """``GET /resources/{resource_code}`` — language-agnostic rollup."""

    resource_code: str
    name: str
    display_name: str
    abbreviation: str | None
    resource_type: str | None
    aquifer_type: str | None
    content_type: str | None
    content_order: ContentOrder | None
    version: str | None
    has_audio: bool
    has_alignments: bool
    license_info: LicenseInfo
    id: int | None
    available_languages: list[ResourceAvailableLanguage]


class ResourceFile(TypedDict):
    path: str
    format: str
    mime_type: str
    size_bytes: int
    books: list[str]
    download_url: str
    group_key: NotRequired[str]  # always present on ``.../files``; absent inside ``by_book``


class ResourceFiles(TypedDict):
    resource_code: str
    language: str
    files: list[ResourceFile]
    alignments: list[ResourceFile]
    audio: list[ResourceFile]


class ResourceByBook(TypedDict):
    book: int
    book_code: str
    reference_count: int | None
    translated_count: int | None
    percent: float | None
    files: list[ResourceFile]
    alignments: list[ResourceFile]
    audio: list[ResourceFile]


class ResourceLanguageDetail(TypedDict):
    """``GET /resources/{resource_code}/{language}`` — one language's detail."""

    resource_code: str
    name: str
    display_name: str
    abbreviation: str | None
    resource_type: str | None
    aquifer_type: str | None
    content_type: str | None
    content_order: ContentOrder | None
    version: str | None
    has_audio: bool
    has_alignments: bool
    license_info: LicenseInfo
    id: int | None
    language: str
    article_count: int
    localization: Localization | None
    download_url: list[str] | None
    release_tag: str | None
    download_urls: DownloadUrls | None
    formats: list[str]
    by_book: NotRequired[list[ResourceByBook]]  # canonical-order resources only
    available_languages: list[str]


class UpdateItem(TypedDict):
    update_type: UpdateType
    language_code: str
    resource_code: str
    content_id: str
    timestamp: str


class UpdatesResponse(TypedDict):
    returned_item_count: int
    total_item_count: int
    offset: int
    items: list[UpdateItem]


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------


class AcaiLink(TypedDict):
    acai_id: str
    entity_type: str
    confidence: float


class SourceFile(TypedDict):
    path: str
    group_key: str


class Deprecation(TypedDict, total=False):
    """Body block on article detail when a renamed ``resource_code`` was requested."""

    resource_code: str
    successor: str
    message: str


class Article(TypedDict):
    """``GET /resources/{resource_code}/{language}/articles/{content_id}``."""

    resource_code: str
    resource_id: str
    resource_name: str
    resource_abbreviation: str
    language_code: str
    content: str | dict[str, Any]  # str for html/markdown, a ProseMirror doc for json
    content_format: ContentFormat
    license_info: LicenseInfo
    acai: list[AcaiLink]
    content_id: str
    title: str
    reference_id: str
    media_type: MediaType
    review_level: ReviewLevel
    index_reference: str | None
    updated_at: str
    deleted_at: str | None
    content_hash: str
    source_file: SourceFile | None
    deprecation: NotRequired[Deprecation]


class PassageAssociation(TypedDict):
    start_book: int
    start_book_code: str
    start_chapter: int
    start_verse: int
    end_book: int
    end_book_code: str
    end_chapter: int
    end_verse: int


class ResourceAssociation(TypedDict):
    content_id: str
    reference_id: str
    display_name: str
    resource_code: str
    language: str


class ArticleLocalization(TypedDict):
    """An article's sibling in another language.

    Same shape on ``.../available-languages`` and in the bulk ``localizations`` join;
    the field names differ slightly between the two, so the optional ones are
    NotRequired.
    """

    language: str
    id: NotRequired[int | None]
    language_name: NotRequired[str]
    content_id: str
    title: str


class BulkArticle(TypedDict):
    """A row of the bulk listing; keys beyond the metadata depend on ``include``."""

    content_id: str
    title: str
    reference_id: str
    media_type: MediaType
    review_level: ReviewLevel
    index_reference: str | None
    updated_at: str
    meaning: str  # always "index-updated"
    deleted: bool
    content: NotRequired[str | dict[str, Any]]
    passage_associations: NotRequired[list[PassageAssociation]]
    resource_associations: NotRequired[list[ResourceAssociation]]
    localizations: NotRequired[list[ArticleLocalization]]
    acai: NotRequired[list[AcaiLink]]


class ArticlesResponse(TypedDict):
    resource_code: str
    language: str
    updated_since: str | None
    include: list[str]
    content_format: ContentFormat | None
    license_info: LicenseInfo
    articles: list[BulkArticle]
    pagination: Pagination


class ArticleAssociations(TypedDict):
    resource_code: str
    language: str
    content_id: str
    passage_associations: list[PassageAssociation]
    resource_associations: list[ResourceAssociation]


class ArticleAvailableLanguages(TypedDict):
    resource_code: str
    language: str
    content_id: str
    available_languages: list[ArticleLocalization]


class SearchResult(TypedDict):
    content_id: str
    title: str
    reference_id: str
    review_level: ReviewLevel
    media_type: MediaType
    language_code: str
    resource_code: str
    resource_name: str
    resource_type: str
    aquifer_type: str
    content_order: ContentOrder | None
    score: NotRequired[float]  # only when ``query`` was given; lower is better


class SearchResponse(TypedDict):
    query: str | None
    results: list[SearchResult]
    pagination: Pagination


# ---------------------------------------------------------------------------
# Tokens (source text and translation)
# ---------------------------------------------------------------------------


class SourceToken(TypedDict):
    """A Greek/Hebrew source-text token (``GET /tokens/{token_id}``)."""

    token_id: str  # ACAI-prefixed ("o…" Hebrew, "n…" Greek)
    corpus: str
    book: int
    chapter: int
    verse: int
    word_num: int
    part: int | None
    text: str
    lemma: str
    strongs: str
    gloss: str
    gloss2: str
    pos: str
    morph: str


class ArticleTokensResponse(TypedDict):
    """Tokens aligned to a lexicon article; unresolvable tokens are bare ``{token_id}``."""

    resource_code: str
    language: str
    content_id: str
    tokens: list[SourceToken]
    pagination: Pagination


class TranslationToken(TypedDict):
    token_id: str
    word_num: int
    book: int
    chapter: int
    verse: int
    text: str
    skip_space_after: bool
    exclude: bool  # true for punctuation
    alignment_status: AlignmentStatus | None  # None when the chapter was never aligned
    record_id: int | None  # non-null only when aligned
    source_verse: str | None
    id_range_end: NotRequired[str]
    source_verse_range_end: NotRequired[str]


class AlignmentSourceToken(TypedDict):
    token_id: str
    corpus: str
    text: str
    lemma: str
    strongs: str
    gloss: str
    gloss2: str
    pos: str
    morph: str
    is_primary: bool


class AlignmentTranslationWord(TypedDict):
    token_id: str
    text: str
    is_primary: bool


class AlignmentTranslation(TypedDict):
    bible_id: str
    words: list[AlignmentTranslationWord]


class LexiconArticleRef(TypedDict):
    lexicon: str
    content_id: str
    title: str


class AlignmentRecord(TypedDict):
    record_id: int | None
    alignment_status: Literal["aligned", "unaligned", "non_equivalent"]
    source: list[AlignmentSourceToken]
    translation: AlignmentTranslation | None  # None for a source-only non-equivalent
    lexicon_articles: list[LexiconArticleRef]
    acai: list[dict[str, Any]]


class PassageTokens(TypedDict):
    passage: str
    bible_id: str
    language: str
    tokens: list[TranslationToken]
    alignment: NotRequired[list[AlignmentRecord]]  # only with include="alignment"


# ---------------------------------------------------------------------------
# Passages
# ---------------------------------------------------------------------------


class PassageArticle(TypedDict):
    content_id: str
    title: str
    index_reference: str | None
    resource_code: str
    start_book: int
    start_chapter: int
    start_verse: int
    end_book: int
    end_chapter: int
    end_verse: int
    content: NotRequired[str | dict[str, Any]]  # only with include_content=True
    density: NotRequired[float]  # only with order="specificity"


class PassageArticlesResponse(TypedDict):
    ref: str
    language: str
    content_format: ContentFormat | None
    articles: list[PassageArticle]
    pagination: Pagination


class ResourceCount(TypedDict):
    resource_type: str
    count: int


class PassageLanguageCounts(TypedDict):
    language: str
    id: int | None
    resource_counts: list[ResourceCount]


class PassageResourceCounts(TypedDict):
    ref: str
    languages: list[PassageLanguageCounts]


# ---------------------------------------------------------------------------
# Bibles
# ---------------------------------------------------------------------------


class BiblesResponse(TypedDict):
    language: str | None
    bibles: list[ResourceSummary]
    pagination: Pagination


class BibleBook(TypedDict):
    book: int
    usfm_code: str
    name: str
    osis_id: str


class BibleBooksResponse(TypedDict):
    books: list[BibleBook]


class AudioFile(TypedDict):
    url: str
    size: int


class ChapterAudio(TypedDict):
    mp3: AudioFile
    webm: AudioFile


class AudioTimestamp(TypedDict):
    start: float
    end: float


class Verse(TypedDict):
    number: int
    text: str
    audio_timestamp: NotRequired[AudioTimestamp | None]


class Chapter(TypedDict):
    number: int
    verses: list[Verse]
    audio: NotRequired[ChapterAudio]


class BibleText(TypedDict):
    """Single-range mode of ``GET /bibles/{bible_id}/texts``."""

    id: int
    bible_id: str
    bible_name: str
    bible_abbreviation: str
    book_name: str
    book_code: str
    language: str
    chapters: list[Chapter]


class BatchVerse(TypedDict):
    ref: str
    book_name: str
    book_code: str
    chapter: int
    verse: int
    text: str
    audio_timestamp: NotRequired[AudioTimestamp | None]


class BibleVerses(TypedDict):
    """``?refs=`` batch mode of ``GET /bibles/{bible_id}/texts``."""

    id: int
    bible_id: str
    bible_name: str
    bible_abbreviation: str
    language: str
    verses: list[BatchVerse]
    missing: list[str]  # requested refs this Bible has no verse for


# ---------------------------------------------------------------------------
# ACAI (biblical-entity registry)
# ---------------------------------------------------------------------------


class AcaiTypeCount(TypedDict):
    type: str
    count: int
    primary_count: int


class AcaiTypesResponse(TypedDict):
    types: list[AcaiTypeCount]


class AcaiEntitySummary(TypedDict):
    acai_id: str
    entity_type: str
    primary_id: str
    is_primary: bool
    preferred_label: str
    label_is_fallback: bool


class AcaiEntitiesResponse(TypedDict):
    type: str | None
    language: str
    include_variants: bool
    entities: list[AcaiEntitySummary]
    pagination: Pagination


class AcaiLocalization(TypedDict):
    language: str
    is_fallback: bool
    preferred_label: str
    description: str | None
    alternate_labels: list[str]


class AcaiRelation(TypedDict):
    relation: str
    target_id: str
    reason: str | None


class AcaiKeyReference(TypedDict):
    ref: str  # BCV8
    book: int
    chapter: int
    verse: int


class AcaiEntity(TypedDict):
    acai_id: str
    primary_id: str
    is_primary: bool
    entity_type: str
    flags: dict[str, bool]
    attributes: dict[str, Any]  # only the non-null keys that apply to the entity type
    localization: AcaiLocalization
    relations: list[AcaiRelation]
    key_references: list[AcaiKeyReference]
    geocoordinates: list[dict[str, Any]]
    place_types: list[str]
    reference_count: int
    speech_count: int
    links: dict[str, str]


class AcaiReference(TypedDict):
    ref: str
    is_key: bool
    book: int | None
    chapter: int | None
    verse: int | None


class AcaiReferencesResponse(TypedDict):
    acai_id: str
    references: list[AcaiReference]
    pagination: Pagination


class AcaiSpeech(TypedDict):
    corpus: str
    speech_index: int
    quote_type: str
    token_ids: list[str]  # resolve with ``get_token``


class AcaiSpeechesResponse(TypedDict):
    acai_id: str
    speeches: list[AcaiSpeech]
    pagination: Pagination


class AcaiToken(TypedDict):
    token_id: str
    corpus: str
    link_type: LinkType
    instance_index: int
    text: str
    lemma: str
    gloss: str


class AcaiTokensResponse(TypedDict):
    acai_id: str
    tokens: list[AcaiToken]
    pagination: Pagination


class AcaiArticle(TypedDict):
    resource_code: str
    language_code: str
    content_id: str
    title: str
    confidence: float


class AcaiArticlesResponse(TypedDict):
    acai_id: str
    articles: list[AcaiArticle]
    pagination: Pagination
