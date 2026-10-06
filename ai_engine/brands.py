"""
brands.py — Indian brand name → generic name + strength normalizer.
Loaded once from brands.csv at import time.
Unknown brand → generic=None (never guesses).
"""
from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_CSV_PATH = Path(__file__).parent / "brands.csv"
_lookup: dict[str, dict] = {}  # normalized_key → {generic, strength}


def _normalize_key(name: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for fuzzy matching."""
    s = re.sub(r"(\d+)\s*(mg|mcg|g|ml|iu)\b", r"\1 \2", name.lower())
    return re.sub(r"[\s\-\.]+", " ", s).strip()


def _load() -> None:
    global _lookup
    if _lookup:
        return
    try:
        with open(_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = _normalize_key(row.get("brand_name", ""))
                if key:
                    _lookup[key] = {
                        "generic": row.get("generic_name", "").strip() or None,
                        "strength": row.get("strength", "").strip() or None,
                    }
        logger.debug("Loaded %d brand entries", len(_lookup))
    except Exception:
        logger.exception("Failed to load brands.csv")


def normalize_brand(name_raw: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Given a raw medicine name string (e.g. "Tab Dolo 650 mg"),
    return (generic_name, strength) or (None, None) if unknown.

    Steps:
    1. Try exact normalized match.
    2. Try stripping common prefixes (Tab, Cap, Inj, Syp, Syr, Oint).
    3. Try without strength suffix (last word if numeric).
    """
    _load()
    raw_norm = _normalize_key(name_raw)

    # Direct match
    if raw_norm in _lookup:
        entry = _lookup[raw_norm]
        return entry["generic"], entry["strength"]

    # Strip tablet/capsule prefix
    cleaned = re.sub(
        r"^(?:tab(?:let)?|cap(?:sule)?|inj(?:ection)?|sy[rp](?:up)?|oint(?:ment)?|susp(?:ension)?)\s+",
        "",
        raw_norm,
    )
    if cleaned in _lookup:
        entry = _lookup[cleaned]
        return entry["generic"], entry["strength"]

    # Also strip unit suffix like "mg", "g", "ml" if present (e.g. "itaspor 200 mg" -> "itaspor 200")
    cleaned_no_unit = re.sub(r"\s*(?:mg|mcg|g|ml|iu)\b", "", cleaned).strip()
    if cleaned_no_unit in _lookup:
        entry = _lookup[cleaned_no_unit]
        return entry["generic"], entry["strength"]

    # Try without trailing strength (e.g. "dolo 650" → "dolo")
    parts = cleaned_no_unit.rsplit(" ", 1)
    if len(parts) == 2 and re.match(r"^\d", parts[1]):
        base = parts[0]
        if base in _lookup:
            entry = _lookup[base]
            return entry["generic"], entry["strength"]

    return None, None
