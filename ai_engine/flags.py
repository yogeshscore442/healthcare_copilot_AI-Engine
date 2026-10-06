"""
flags.py — Deterministic abnormal flag computation.
LLM NEVER calls this module or influences its output.
Flags are always LOW / NORMAL / HIGH / UNKNOWN.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_RANGES_PATH = Path(__file__).parent / "reference_ranges.json"
_ranges_data: dict = {}


def _load() -> dict:
    global _ranges_data
    if not _ranges_data:
        with open(_RANGES_PATH, encoding="utf-8") as f:
            _ranges_data = json.load(f)["tests"]
    return _ranges_data


def _normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/spaces for lookup."""
    return re.sub(r"[^a-z0-9]", " ", name.lower()).strip()


def lookup_reference(test_name: str, sex: Optional[str] = None) -> Optional[dict]:
    """
    Find a reference-range entry for the given test name.
    sex: 'M', 'F', or None (falls back to male range or unsexed range).
    Returns the matching entry dict, or None if not found.
    """
    ranges = _load()
    norm = _normalize_name(test_name)

    candidates = []
    for key, entry in ranges.items():
        for alias in entry.get("aliases", []):
            if _normalize_name(alias) == norm:
                candidates.append((key, entry))
                break

    if not candidates:
        return None

    # If sex-specific variants exist, prefer the matching one
    if sex:
        sex_upper = sex.upper()
        for key, entry in candidates:
            if entry.get("sex", "").upper() == sex_upper:
                return entry
    # Default: first match (typically male or unsexed)
    return candidates[0][1]


def normalize_unit(value: float, from_unit: str, entry: dict) -> float:
    """
    Convert mmol/L → mg/dL when needed, using the mmol_factor in the entry.
    Returns value in the canonical unit; raises ValueError if unit unknown.
    """
    from_norm = from_unit.lower().strip()
    canonical = entry.get("unit", "").lower()
    aliases = [u.lower() for u in entry.get("unit_aliases", [])]

    # Already in canonical unit
    if from_norm in aliases or from_norm == canonical:
        return value

    # mmol/L → mg/dL conversion
    mmol_factor = entry.get("mmol_factor")
    if mmol_factor and "mmol" in from_norm:
        return value * mmol_factor

    # Unknown unit — can't normalize
    raise ValueError(f"Cannot normalize unit '{from_unit}' for test '{entry}'")


def compute_flag(
    test_name: str,
    value: Optional[float],
    unit: Optional[str],
    ref_low: Optional[float],
    ref_high: Optional[float],
    sex: Optional[str] = None,
) -> str:
    """
    Compute LOW / NORMAL / HIGH / UNKNOWN deterministically.

    Priority:
    1. Use ref_low / ref_high from the document itself if both are present.
    2. Look up reference_ranges.json.
    3. If value is None or no range found → UNKNOWN.
    """
    if value is None:
        return "UNKNOWN"

    # Prefer document's own range
    if ref_low is not None or ref_high is not None:
        return _flag_from_range(value, ref_low, ref_high)

    # Fall back to built-in table
    try:
        entry = lookup_reference(test_name, sex=sex)
        if entry is None:
            return "UNKNOWN"

        # Unit normalization
        conv_value = value
        if unit:
            try:
                conv_value = normalize_unit(value, unit, entry)
            except ValueError:
                logger.warning(
                    "Unit mismatch for '%s': unit='%s', expected='%s'. Using raw value.",
                    test_name, unit, entry.get("unit"),
                )

        return _flag_from_range(conv_value, entry.get("ref_low"), entry.get("ref_high"))

    except Exception:
        logger.exception("Flag computation failed for '%s'", test_name)
        return "UNKNOWN"


def _flag_from_range(
    value: float,
    ref_low: Optional[float],
    ref_high: Optional[float],
) -> str:
    if ref_low is not None and value < ref_low:
        return "LOW"
    if ref_high is not None and value > ref_high:
        return "HIGH"
    if ref_low is None and ref_high is None:
        return "UNKNOWN"
    return "NORMAL"


def get_loinc(test_name: str, sex: Optional[str] = None) -> Optional[str]:
    """Return LOINC code for a test name, or None."""
    entry = lookup_reference(test_name, sex=sex)
    return entry.get("loinc") if entry else None
