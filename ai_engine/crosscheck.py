"""
crosscheck.py — Cross-verifies LLM extracted entities against local OCR text.
Adjusts confidence scores and triggers needs_review without logging any patient content.
"""
from __future__ import annotations

import difflib
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Metrics counter (log counts only, never patient content)
_STATS = {
    "test_found": 0,
    "test_not_found": 0,
    "med_found": 0,
    "med_not_found": 0,
    "crosscheck_skipped": 0,
}


def get_crosscheck_stats() -> Dict[str, int]:
    return dict(_STATS)


def _is_tamil_or_non_ascii(text: str) -> bool:
    """Returns True if text contains significant Tamil/non-ASCII characters."""
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))
    return tamil_chars > 5


def _fuzzy_match(query: str, target: str, threshold: float = 0.75) -> bool:
    """Check if query is present in target or fuzzy matches any token in target."""
    q = query.lower().strip()
    t = target.lower()
    if q in t:
        return True
    
    # Check word-level match or token-level fuzzy match
    target_words = re.findall(r"[a-z0-9]{3,}", t)
    for w in target_words:
        ratio = difflib.SequenceMatcher(None, q, w).ratio()
        if ratio >= threshold:
            return True
    return False


def _number_present_in_ocr(val: float, ocr_text: str) -> bool:
    """Check if numeric value appears in OCR text, handling decimals and commas."""
    # Normalize OCR text
    clean_ocr = ocr_text.replace(",", ".")
    # Match integer or float
    if val.is_integer():
        patterns = [rf"\b{int(val)}\b", rf"\b{int(val)}\.0\b"]
    else:
        # e.g. 10.2 -> match 10.2 or 10,2
        val_str = str(val)
        patterns = [rf"\b{re.escape(val_str)}\b"]

    for pat in patterns:
        if re.search(pat, clean_ocr):
            return True
    return False


def crosscheck_record(record: dict, ocr_text: Optional[str]) -> dict:
    """
    Cross-checks numeric tests and medicines against raw OCR text.
    Modifies confidence and needs_review in-place.
    Skips if OCR text is empty, short, or Tamil script.
    """
    if not ocr_text or len(ocr_text.strip()) < 30 or _is_tamil_or_non_ascii(ocr_text):
        _STATS["crosscheck_skipped"] += 1
        logger.info("crosscheck_skipped count=%d", _STATS["crosscheck_skipped"])
        return record

    needs_review = list(record.get("needs_review", []))

    # 1. Tests cross-check
    for i, test in enumerate(record.get("tests", [])):
        val = test.get("value")
        if val is not None and isinstance(val, (int, float)):
            found = _number_present_in_ocr(float(val), ocr_text)
            if found:
                _STATS["test_found"] += 1
                test["confidence"] = min(1.0, round(test.get("confidence", 0.9) + 0.05, 2))
            else:
                _STATS["test_not_found"] += 1
                test["confidence"] = max(0.3, round(test.get("confidence", 0.9) - 0.20, 2))
                path = f"tests[{i}]"
                if path not in needs_review:
                    needs_review.append(path)

    # 2. Medicines cross-check
    for i, med in enumerate(record.get("medicines", [])):
        name_raw = med.get("name_raw", "")
        # Clean brand prefix like "Tab. ", "Cap. "
        clean_name = re.sub(r"^(?:tab|cap|syp|inj)\.?\s*", "", name_raw, flags=re.IGNORECASE).strip()
        first_token = clean_name.split()[0] if clean_name else ""
        if len(first_token) >= 3:
            found = _fuzzy_match(first_token, ocr_text, threshold=0.80)
            if found:
                _STATS["med_found"] += 1
                med["confidence"] = min(1.0, round(med.get("confidence", 0.9) + 0.05, 2))
            else:
                _STATS["med_not_found"] += 1
                med["confidence"] = max(0.3, round(med.get("confidence", 0.9) - 0.20, 2))
                path = f"medicines[{i}]"
                if path not in needs_review:
                    needs_review.append(path)

    record["needs_review"] = needs_review
    logger.info(
        "Crosscheck complete: test_found=%d test_not_found=%d med_found=%d med_not_found=%d",
        _STATS["test_found"], _STATS["test_not_found"], _STATS["med_found"], _STATS["med_not_found"]
    )
    return record
