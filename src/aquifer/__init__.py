"""aquifer — Python client for the Aquifer Bible API.

Quickstart::

    from aquifer import AquiferClient

    with AquiferClient.from_env() as client:
        bibles = client.get_all_bibles(language_code="eng")
        text = client.get_bible_book_text(bibles[0]["id"], "MAT", audio=True)
"""

from importlib.metadata import PackageNotFoundError, version

from aquifer.bible_books import (
    APOCRYPHA_BOOKS,
    NT_BOOKS,
    OT_BOOKS,
    USFM_BOOK_CODES,
    book_is_apocrypha,
    book_is_nt,
    book_is_ot,
    canonical_order,
)
from aquifer.client import BASE_URL, AquiferClient
from aquifer.languages import LANGUAGES, LanguageInfo, get_language, is_rtl
from aquifer.models import (
    AlignmentChapter,
    AlignmentVerse,
    AlignmentWord,
    Associations,
    AudioData,
    AudioFile,
    AudioTimestamp,
    Bible,
    BibleBook,
    BibleBookText,
    BibleLicenseInfo,
    Chapter,
    CollectionLanguage,
    ContentTextType,
    Copyright,
    CopyrightHolder,
    GreekAlignment,
    GreekWord,
    GreekWordSense,
    Language,
    LanguageAvailableResources,
    LicenseEntry,
    LicenseInfo,
    MediaType,
    PassageAssociation,
    Resource,
    ResourceAssociationRef,
    ResourceAvailableLanguage,
    ResourceCollectionDetail,
    ResourceCollectionSummary,
    ResourceCount,
    ResourceGrouping,
    ResourceGroupingFull,
    ResourceSearchResult,
    ResourceSummary,
    ResourceType,
    ResourceTypeCollection,
    ResourceTypeGroup,
    ResourceUpdate,
    ResourceUpdatesResult,
    ReviewLevel,
    ScriptDirection,
    UpdateType,
    Verse,
)

try:
    __version__ = version("aquifer-api-client")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    # Client
    "AquiferClient",
    "BASE_URL",
    # Literal / enum types
    "ContentTextType",
    "MediaType",
    "ResourceType",
    "ReviewLevel",
    "ScriptDirection",
    "UpdateType",
    # Bible text models
    "AudioData",
    "AudioFile",
    "AudioTimestamp",
    "Bible",
    "BibleBook",
    "BibleBookText",
    "BibleLicenseInfo",
    "Chapter",
    "Verse",
    # Greek alignment models
    "AlignmentChapter",
    "AlignmentVerse",
    "AlignmentWord",
    "GreekAlignment",
    "GreekWord",
    "GreekWordSense",
    # Resource models
    "Associations",
    "AssociatedResource",
    "CollectionLanguage",
    "Copyright",
    "CopyrightHolder",
    "Language",
    "LanguageAvailableResources",
    "LicenseEntry",
    "LicenseInfo",
    "PassageAssociation",
    "Resource",
    "ResourceAssociationRef",
    "ResourceAvailableLanguage",
    "ResourceCollectionDetail",
    "ResourceCollectionSummary",
    "ResourceCount",
    "ResourceGrouping",
    "ResourceGroupingFull",
    "ResourceSearchResult",
    "ResourceSummary",
    "ResourceTypeCollection",
    "ResourceTypeGroup",
    "ResourceUpdate",
    "ResourceUpdatesResult",
    # Language helpers
    "LANGUAGES",
    "LanguageInfo",
    "get_language",
    "is_rtl",
    # Bible book helpers
    "APOCRYPHA_BOOKS",
    "NT_BOOKS",
    "OT_BOOKS",
    "USFM_BOOK_CODES",
    "book_is_apocrypha",
    "book_is_nt",
    "book_is_ot",
    "canonical_order",
]
