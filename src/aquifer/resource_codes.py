"""Renamed ``resource_code`` values.

Seven source repos were renamed upstream. The v2 API still accepts the old codes (the
response uses the current code and carries a ``Deprecation`` header), but stored codes
should be migrated.
"""

from __future__ import annotations

RESOURCE_CODE_RENAMES: dict[str, str] = {
    "TyndaleBibleDictionary": "AquiferOpenBibleDictionary",
    "TyndaleStudyNotes": "AquiferOpenStudyNotes",
    "TyndaleStudyNotesBookIntros": "AquiferOpenStudyNotesBookIntros",
    "TyndaleStudyNotesBookIntroSummaries": "AquiferOpenStudyNotesBookIntroSummaries",
    "TyndaleStudyNotesProfiles": "AquiferOpenStudyNotesProfiles",
    "TyndaleStudyNotesThemes": "AquiferOpenStudyNotesThemes",
    "CBBTER": "FIATranslationGuide",
    "UbsImages": "UBSImages",
}


def current_resource_code(code: str) -> str:
    """Return the current form of ``code``, or ``code`` itself if it was never renamed."""
    return RESOURCE_CODE_RENAMES.get(code, code)
