"""
diagnoses.py — ICD-10 medical terminology resolution and clinical normalization.
Grounded in authoritative WHO / ICD-10-CM clinical coding standards.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_ICD10_PATH = Path(__file__).parent / "icd10.json"
_icd10_data: dict = {}


def _normalize_term(term: str) -> str:
    """Lowercase and remove excess punctuation for fuzzy match."""
    s = re.sub(r"[^a-z0-9]", " ", term.lower())
    return re.sub(r"\s+", " ", s).strip()


def _load() -> dict:
    global _icd10_data
    if not _icd10_data:
        try:
            with open(_ICD10_PATH, encoding="utf-8") as f:
                raw = json.load(f).get("conditions", {})
                _icd10_data = {_normalize_term(k): v for k, v in raw.items()}
        except Exception as e:
            logger.warning("Could not load icd10.json: %s", e)
            _icd10_data = {}
    return _icd10_data


def lookup_icd10(diagnosis_text: str) -> Optional[Tuple[str, str]]:
    """
    Look up ICD-10 code and formal display name for a clinical diagnosis string.
    Returns (icd10_code, display_name) or None if no match.
    """
    if not diagnosis_text:
        return None
    data = _load()
    norm_diag = _normalize_term(diagnosis_text)

    # 1. Exact normalized match
    if norm_diag in data:
        entry = data[norm_diag]
        return entry.get("icd10"), entry.get("display")

    # 2. Substring matching
    for key, entry in data.items():
        if key in norm_diag or norm_diag in key:
            return entry.get("icd10"), entry.get("display")

    return None
