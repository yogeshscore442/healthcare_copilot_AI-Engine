"""
dosage.py — Parse Indian medical dosage strings into structured fields.

Handles:
  1-0-1, 1-1-1, 0-0-1, 1-0-0 etc.      → schedule_parsed
  OD, BD, TDS, QID, HS, SOS             → schedule_parsed
  before food / after food / AC / PC    → food_instruction
  x 5 days / for 5 days / 5 days        → duration_days

Returns:
  (schedule_parsed: list[str], food_instruction: str|None, duration_days: int|None)
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# Slot positions in N-N-N patterns
_SLOTS = ["morning", "afternoon", "night"]

# Abbreviation → slots
_ABBREV: dict[str, list[str]] = {
    "od":  ["morning"],
    "bd":  ["morning", "night"],
    "tds": ["morning", "afternoon", "night"],
    "tid": ["morning", "afternoon", "night"],
    "qid": ["morning", "afternoon", "night"],   # 4× treated as M+A+N for display
    "hs":  ["night"],
    "sos": [],
    "prn": [],
    "stat": ["morning"],
    "nocte": ["night"],
    "mane": ["morning"],
}

_FOOD_BEFORE = re.compile(
    r"\b(?:before\s+food|before\s+meal|a\.?c\.?|ac\b|empty\s+stomach)\b",
    re.IGNORECASE,
)
_FOOD_AFTER = re.compile(
    r"\b(?:after\s+food|after\s+meal|p\.?c\.?|pc\b|with\s+food)\b",
    re.IGNORECASE,
)
_DURATION = re.compile(
    r"(?:x\s*|for\s+)?(\d+)\s*(?:days?|d\b)",
    re.IGNORECASE,
)
_DASH_PATTERN = re.compile(r"^(\d)-(\d)-(\d)(?:-(\d))?$")
_ABBREV_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _ABBREV) + r")\b",
    re.IGNORECASE,
)


def parse_schedule(schedule_raw: Optional[str]) -> Tuple[list, Optional[str], Optional[int]]:
    """
    Parse *schedule_raw* string into:
        schedule_parsed  : list of "morning" | "afternoon" | "night"
        food_instruction : "before_food" | "after_food" | None
        duration_days    : int | None

    Examples:
        "1-0-1 after food x 5 days" → (["morning","night"], "after_food", 5)
        "BD" → (["morning","night"], None, None)
        "TDS AC" → (["morning","afternoon","night"], "before_food", None)
        "" / None → ([], None, None)
    """
    if not schedule_raw or not schedule_raw.strip():
        return [], None, None

    text = schedule_raw.strip()

    # ── Food instruction ──────────────────────────────────────────────────────
    food: Optional[str] = None
    if _FOOD_BEFORE.search(text):
        food = "before_food"
    elif _FOOD_AFTER.search(text):
        food = "after_food"

    # ── Duration ──────────────────────────────────────────────────────────────
    duration: Optional[int] = None
    dur_match = _DURATION.search(text)
    if dur_match:
        try:
            duration = int(dur_match.group(1))
        except ValueError:
            pass

    # ── Schedule slots ────────────────────────────────────────────────────────
    slots: list[str] = []

    # Try N-N-N dash pattern first (highest priority)
    dash_match = _DASH_PATTERN.match(text.split()[0])
    if dash_match:
        for i, grp in enumerate(_SLOTS):
            val = dash_match.group(i + 1)
            if val and val != "0":
                slots.append(grp)
    else:
        # Try abbreviation
        abbrev_match = _ABBREV_PATTERN.search(text)
        if abbrev_match:
            key = abbrev_match.group(1).lower()
            slots = list(_ABBREV.get(key, []))

    return slots, food, duration


def parse_all(name_raw: str, schedule_raw: Optional[str]) -> dict:
    """
    Convenience wrapper returning a dict ready to merge into a MedicineRecord.
    """
    slots, food, dur = parse_schedule(schedule_raw)
    return {
        "schedule_parsed": slots,
        "food_instruction": food,
        "duration_days": dur,
    }
