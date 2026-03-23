"""Typed response models for the Aquifer API.

All models are TypedDict — they are plain dicts at runtime with no parsing
overhead. Fields marked NotRequired may be absent from the response.
"""

from typing import Any, Literal, NotRequired, TypedDict

# ---------------------------------------------------------------------------
# Literal enums
# ---------------------------------------------------------------------------

ResourceType = Literal["None", "Guide", "Dictionary", "StudyNotes", "Images", "Videos"]
ReviewLevel = Literal["None", "Community", "Professional", "Ai"]
MediaType = Literal["None", "Text", "Audio", "Video", "Image"]
ScriptDirection = Literal["None", "LTR", "RTL"]
UpdateType = Literal["New", "Updated"]
ContentTextType = Literal["None", "Json", "Html", "Markdown"]

# ---------------------------------------------------------------------------
# Shared / license structures
# ---------------------------------------------------------------------------


class CopyrightHolder(TypedDict):
    name: str
    url: str


class Copyright(TypedDict):
    dates: str | None
    holder: CopyrightHolder


class LicenseEntry(TypedDict):
    eng: dict[str, str]  # {"name": "...", "url": "..."}


class LicenseInfo(TypedDict):
    title: str
    copyright: Copyright
    licenses: list[LicenseEntry]
    showAdaptationNoticeForEnglish: bool
    showAdaptationNoticeForNonEnglish: bool


class BibleLicenseInfo(TypedDict):
    """License info as returned on Bible objects (no adaptation-notice flags)."""
    title: str
    copyright: Copyright
    licenses: list[LicenseEntry]


# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------


class Language(TypedDict):
    id: int
    code: str                        # ISO 639-3, e.g. "eng"
    englishDisplay: str
    localizedDisplay: str
    scriptDirection: ScriptDirection


class ResourceCount(TypedDict):
    type: str
    count: int


class LanguageAvailableResources(TypedDict):
    """Resource counts per type for a language at a given Bible passage."""
    languageId: int
    languageCode: str
    resourceCounts: list[ResourceCount]


# ---------------------------------------------------------------------------
# Bibles
# ---------------------------------------------------------------------------


class Bible(TypedDict):
    id: int
    name: str
    abbreviation: str
    languageId: int
    isLanguageDefault: bool
    hasAudio: bool
    hasGreekAlignment: bool
    licenseInfo: BibleLicenseInfo


class BibleBook(TypedDict):
    """Entry from the global /bibles/books list."""
    name: str
    code: str   # USFM book code, e.g. "MAT"


# ---------------------------------------------------------------------------
# Bible text
# ---------------------------------------------------------------------------


class AudioFile(TypedDict):
    url: str
    size: int


class AudioData(TypedDict):
    webm: AudioFile | None
    mp3: AudioFile | None


class AudioTimestamp(TypedDict):
    start: float
    end: float


class Verse(TypedDict):
    number: int
    text: str
    audioTimestamp: NotRequired[AudioTimestamp | None]


class Chapter(TypedDict):
    number: int
    verses: list[Verse]
    audio: NotRequired[AudioData | None]


class BibleBookText(TypedDict):
    bibleId: int
    bibleName: str
    bibleAbbreviation: str
    bookName: str
    bookCode: str
    chapters: list[Chapter]


# ---------------------------------------------------------------------------
# Greek alignment
# ---------------------------------------------------------------------------


class GreekWordSense(TypedDict):
    glosses: list[str]
    definition: str


class GreekWord(TypedDict):
    word: str
    grammarType: str
    usageCode: str
    lemma: str
    strongsNumber: str
    senses: NotRequired[list[GreekWordSense] | None]


class AlignmentWord(TypedDict):
    number: int
    word: str
    nextWordIsInGroup: bool
    greekWords: list[GreekWord]


class AlignmentVerse(TypedDict):
    number: int
    words: list[AlignmentWord]


class AlignmentChapter(TypedDict):
    number: int
    verses: list[AlignmentVerse]


class GreekAlignment(TypedDict):
    bibleId: int
    bibleName: str
    bibleAbbreviation: str
    greekBibleAbbreviation: str
    bookName: str
    bookCode: str
    chapters: list[AlignmentChapter]


# ---------------------------------------------------------------------------
# Resources — search / list
# ---------------------------------------------------------------------------


class ResourceGrouping(TypedDict):
    """Grouping metadata on a ResourceSummary (search result)."""
    type: str
    collectionCode: str
    collectionTitle: str


class ResourceSummary(TypedDict):
    """One item returned by /resources/search."""
    id: int
    name: str
    localizedName: str
    reviewLevel: ReviewLevel
    mediaType: MediaType
    languageCode: str
    grouping: ResourceGrouping


class ResourceSearchResult(TypedDict):
    totalItemCount: int
    returnedItemCount: int
    offset: int
    items: list[ResourceSummary]


# ---------------------------------------------------------------------------
# Resources — detail
# ---------------------------------------------------------------------------


class AssociatedResource(TypedDict):
    id: int
    name: str
    localizedName: str


class ResourceGroupingFull(TypedDict):
    """Grouping metadata on a full Resource (includes associated resources)."""
    type: str
    collectionCode: str
    collectionTitle: str
    associatedResources: list[AssociatedResource]


class Resource(TypedDict):
    """Full resource as returned by /resources/{contentId}.

    The ``content`` field format depends on the ``text_type`` requested:
    - ``"Html"`` / ``"Markdown"``: ``str`` or ``list[str]`` for multi-section resources
    - ``"Json"`` (TipTap): ``dict[str, Any]``
    - ``"None"``: ``None``
    """
    id: int
    referenceId: int
    name: str
    localizedName: str
    reviewLevel: ReviewLevel
    content: Any
    grouping: ResourceGroupingFull
    language: Language


# ---------------------------------------------------------------------------
# Resources — available languages / associations
# ---------------------------------------------------------------------------


class ResourceAvailableLanguage(TypedDict):
    contentId: int
    contentDisplayName: str
    languageId: int
    languageDisplayName: str
    languageEnglishDisplayName: str
    languageCode: str


class PassageAssociation(TypedDict):
    startBookCode: str
    startChapter: int
    startVerse: int
    endBookCode: str
    endChapter: int
    endVerse: int


class ResourceAssociationRef(TypedDict):
    contentId: int
    displayName: str
    referenceId: int


class Associations(TypedDict):
    passageAssociations: list[PassageAssociation]
    resourceAssociations: list[ResourceAssociationRef]


# ---------------------------------------------------------------------------
# Resource updates
# ---------------------------------------------------------------------------


class ResourceUpdate(TypedDict):
    updateType: UpdateType
    languageId: int
    languageCode: str
    resourceId: int
    timestamp: str   # ISO 8601 datetime string


class ResourceUpdatesResult(TypedDict):
    returnedItemCount: int
    totalItemCount: int
    offset: int
    items: list[ResourceUpdate]


# ---------------------------------------------------------------------------
# Resource types
# ---------------------------------------------------------------------------


class ResourceTypeCollection(TypedDict):
    code: str
    title: str
    licenseInformation: LicenseInfo


class ResourceTypeGroup(TypedDict):
    type: str
    collections: list[ResourceTypeCollection]


# ---------------------------------------------------------------------------
# Resource collections
# ---------------------------------------------------------------------------


class ResourceCollectionSummary(TypedDict):
    code: str
    displayName: str
    shortName: str
    resourceType: ResourceType
    sliCategory: str | None
    sliLevel: int | None


class CollectionLanguage(TypedDict):
    languageId: int
    languageCode: str
    displayName: str
    resourceItemCount: int


class ResourceCollectionDetail(TypedDict):
    code: str
    displayName: str
    shortName: str
    resourceType: ResourceType
    sliCategory: str | None
    sliLevel: int | None
    licenseInfo: LicenseInfo
    availableLanguages: list[CollectionLanguage]
