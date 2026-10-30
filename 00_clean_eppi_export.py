"""
00_clean_eppi_export.py
=======================
Optional preparatory step. Writes a public copy of an EPPI-Reviewer JSON
export that keeps only what the pipeline needs plus the bibliographic details
that identify each study. This is how the files in data/ were produced from
the original exports.

Kept per reference
------------------
ItemId, OldItemId, Title, ShortTitle, Authors, ParentTitle (journal), Year,
Volume, Issue, Pages, DOI, URL, StandardNumber (ISSN), TypeName,
QuickCitation, Abstract (as retrieved from MEDLINE or Embase) and Codes (the
coding itself).

Removed per reference
---------------------
Every other field, in particular Comments, Keywords, Institution, CreatedBy,
EditedBy, DateCreated, DateEdited and the item status fields. The codeset (CodeSets) is kept unchanged.

Usage
-----
    python 00_clean_eppi_export.py <export.json> <public_copy.json>
"""

import json
import sys

KEEP_FIELDS = [
    "ItemId", "OldItemId", "Title", "ShortTitle", "Authors", "ParentTitle",
    "Year", "Volume", "Issue", "Pages", "DOI", "URL", "StandardNumber",
    "TypeName", "QuickCitation", "Abstract", "Codes",
]


def clean_reference(ref: dict) -> dict:
    """Return a copy of one reference restricted to KEEP_FIELDS, in that order."""
    return {k: ref[k] for k in KEEP_FIELDS if k in ref}


def main() -> None:
    """Command-line entry point: read the export, clean it and write the copy."""
    if len(sys.argv) != 3:
        print("Usage: python 00_clean_eppi_export.py <export.json> <public_copy.json>")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        data = json.load(fh)
    cleaned = {
        "CodeSets": data["CodeSets"],
        "References": [clean_reference(r) for r in data["References"]],
    }
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(cleaned, fh, ensure_ascii=False, indent=1)
    print(f"Wrote {len(cleaned['References'])} references to {dst}")


if __name__ == "__main__":
    main()
