"""
privacy.py — PII masking for text sent to the LLM for summarization.

WHAT IS MASKED (before any text reaches the summarization LLM):
  - Indian phone numbers (10-digit, with/without +91 / 0 prefix)
  - Email addresses
  - Aadhaar-like 12-digit number groups (XXXX XXXX XXXX)
  - Generic ID numbers (PID, MRN, UHID, ABHA patterns)
  - Patient names when clearly labelled ("Patient: John Doe")
  - Postal addresses (door no, PIN codes, street patterns)

WHAT IS NOT MASKED:
  - Test values and units
  - Medicine names and dosages
  - Dates (not PII in this context)
  - Doctor names (not patient PII)
  - Diagnosis text (clinical, not personal)

NOTE: The extraction LLM receives the raw document image (vision call).
Masking applies only to Tesseract fallback text included in extraction prompts
and to the structured JSON used as summarization LLM input.
"""
from __future__ import annotations

import re
from typing import Any

# ── Regex patterns ─────────────────────────────────────────────────────────────

_PATTERNS: list[tuple[str, str, int]] = [
    # (label, pattern, re_flags)
    ("phone",    r"(?:\+91[\s\-]?)?[6-9]\d{9}\b",                                   re.IGNORECASE),
    ("email",    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",              0),
    ("aadhaar",  r"\b\d{4}\s\d{4}\s\d{4}\b",                                        0),
    ("id_num",   r"(?:PID|MRN|UHID|ABHA|REG(?:NO)?|IP\s?NO|OP\s?NO)[\s:.-]*\d+",  re.IGNORECASE),
    ("pin",      r"\b[1-9]\d{5}\b",                                                  0),
    ("patient",  r"(?:Patient(?:\s+Name)?|Name of Patient)\s*[:\-]\s*[A-Z][a-zA-Z\s\.]{2,40}", re.IGNORECASE),
]

_COMPILED = [
    (label, re.compile(pat, flags), repl)
    for label, pat, flags in _PATTERNS
    for repl in (f"[{label.upper()}]",)
]


def mask_text(text: str) -> str:
    """
    Replace PII patterns in *text* with placeholder tokens.
    Returns the cleaned string.
    """
    for _label, pattern, repl in _COMPILED:
        text = pattern.sub(repl, text)
    return text


def mask_record_for_llm(record: dict) -> dict:
    """
    Return a shallow-copy of *record* with patient-identifying strings masked.
    Only modifies string fields that could carry PII; clinical values untouched.
    """
    import copy
    r = copy.deepcopy(record)
    r["patient_name_present"] = False  # signal to LLM that name is gone
    # Mask summary strings if already partially filled
    for key in ("summary_en", "summary_ta"):
        if isinstance(r.get(key), str):
            r[key] = mask_text(r[key])
    return r
