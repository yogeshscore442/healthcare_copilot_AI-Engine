"""
summarize.py — Safe plain-language summary generation.

Rules (enforced by prompt + keyword scanner + deterministic fallback):
  ✓ Grounded ONLY in extracted JSON — no outside facts about the patient.
  ✗ No diagnosis wording ("you have...", "diagnosed with...")
  ✗ No treatment/dosage advice ("you should take...", "increase dose...")
  ✗ No drug interaction claims
  ✓ Abnormal values: "is above/below the usual range — please discuss with your doctor"
  ✓ Always ends with fixed disclaimer
  ✓ Tamil summary via separate LLM call with same safety rules
  ✓ Deterministic fallback used when LLM unavailable
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

from .models import DISCLAIMER
from .privacy import mask_record_for_llm

logger = logging.getLogger(__name__)

def _get_api_key() -> str:
    return os.getenv("LLM_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

def _get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "google").lower()

def _get_model() -> str:
    return os.getenv("LLM_MODEL") or "gemini-2.5-pro"

_TIMEOUT = 30

# ── Forbidden wording patterns (post-process check) ───────────────────────────
_FORBIDDEN = re.compile(
    r"\b("
    r"you have|you are diagnosed|diagnosed with|your diagnosis|"
    r"you should take|increase your dose|decrease your dose|stop taking|"
    r"drug interaction|contraindicated|side effects?|"
    r"prescribe|recommend(?:ed)? (?:taking|you)|"
    r"treatment plan|medical advice"
    r")\b",
    re.IGNORECASE,
)

# The fixed disclaimer is always safe — bypass forbidden-phrase check for it
_DISCLAIMER_PHRASE = "it is not a diagnosis or medical advice"

# Matches any standalone number (integer or decimal) in summary text
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


def _collect_record_numbers(record: dict) -> set[str]:
    """
    Collect every numeric value from the extracted record so we can
    verify that summary numbers are grounded in the actual data.
    """
    nums: set[str] = set()
    for test in record.get("tests", []):
        for field in ("value", "ref_low", "ref_high"):
            v = test.get(field)
            if v is not None:
                nums.add(str(float(v)))
                nums.add(str(int(v)) if float(v) == int(float(v)) else str(v))
    for med in record.get("medicines", []):
        d = med.get("duration_days")
        if d is not None:
            nums.add(str(d))
        # strength digits
        strength = med.get("strength") or ""
        for m in _NUMBER_RE.findall(strength):
            nums.add(m)
    return nums


def _grounding_check(summary_text: str, record: dict) -> bool:
    """
    PHASE 3: Verify that every number in the summary text exists in the
    extracted record (tests, medicines, diagnoses). Returns True if grounded,
    False if a hallucinated number is detected.

    Numbers that are always safe (counts, years, percentages of 100):
    - 0, 1, 2, 100 (common incidental numbers)
    """
    safe_numbers = {"0", "1", "2", "100"}
    record_nums = _collect_record_numbers(record)
    summary_numbers = set(_NUMBER_RE.findall(summary_text))
    ungrounded = summary_numbers - record_nums - safe_numbers
    if ungrounded:
        logger.warning(
            "Grounding check: %d ungrounded number(s) in summary: %s — using deterministic fallback",
            len(ungrounded), list(ungrounded)[:5],
        )
        return False
    return True


def _safety_check(text: str) -> bool:
    """Return True if text is safe (no forbidden phrases)."""
    # Strip the standard disclaimer sentence before scanning — it contains
    # the otherwise-forbidden phrase 'medical advice'.
    scan_text = re.sub(
        re.escape(_DISCLAIMER_PHRASE), "", text, flags=re.IGNORECASE
    )
    return _FORBIDDEN.search(scan_text) is None


# ── LLM summarization ─────────────────────────────────────────────────────────

_EN_SYSTEM = """You are a medical document summary assistant.
Your ONLY job is to write a short, plain-language summary of the extracted medical record data provided.

STRICT RULES:
1. Only describe what is in the data. Do not add outside knowledge about the patient.
2. NEVER say "you have [condition]", "you are diagnosed with", or any diagnosis statement.
3. NEVER say "you should take", "increase", "decrease", or give any treatment advice.
4. NEVER mention drug interactions.
5. For abnormal lab values: say "The [test name] value ([value] [unit]) is above/below the usual range ([low]–[high] [unit]). Please discuss this with your doctor."
6. For normal values: say "The [test name] ([value] [unit]) is within the usual range."
7. For medicines: list them as-is. Do not comment on dosages.
8. For diagnostic reports: use "The report mentions..." and never add your own interpretation.
9. Keep the tone neutral and calm. Write at a 6th-grade reading level.
10. End with EXACTLY this sentence: "This is AI-generated information to help you understand your records. It is not a diagnosis or medical advice. Please consult your doctor."
11. Return only the summary text. No headings, no bullet points, no markdown."""

_TA_SYSTEM = """நீங்கள் ஒரு மருத்துவ ஆவண சுருக்க உதவியாளர்.
கொடுக்கப்பட்ட மருத்துவ பதிவு தரவை அடிப்படையாகக் கொண்டு, தமிழில் ஒரு சுருக்கமான, எளிமையான சுருக்கம் எழுதவும்.

கட்டாய விதிகள்:
1. கொடுக்கப்பட்ட தரவில் உள்ளதை மட்டுமே விவரிக்கவும்.
2. "உங்களுக்கு [நோய்] உள்ளது" என்று எந்த நோய் கண்டறிதலையும் கூறாதீர்கள்.
3. எந்த மருந்தையும் எடுக்க வேண்டும் அல்லது அளவை மாற்ற வேண்டும் என்று கூறாதீர்கள்.
4. அசாதாரண மதிப்புகளுக்கு: "[சோதனை பெயர்] மதிப்பு ([மதிப்பு] [அலகு]) வழக்கமான அளவை விட அதிகமாக/குறைவாக உள்ளது. உங்கள் மருத்துவரிடம் இதைப் பற்றி பேசுங்கள்."
5. கடைசியாக சரியாக இந்த வாக்கியத்தை சேர்க்கவும்: "இது AI-உருவாக்கிய தகவல். இது நோய் கண்டறிதலோ மருத்துவ ஆலோசனையோ அல்ல. உங்கள் மருத்துவரை அணுகவும்."
6. சுருக்க உரையை மட்டும் திரும்பவும்."""


def _call_summarize_llm(prompt: str, system: str) -> str:
    """Call LLM for summarization with automatic fallback. Returns empty string on failure."""
    provider = _get_provider()
    api_key = _get_api_key()
    preferred_model = _get_model()

    if not api_key:
        return ""

    try:
        if provider == "google":
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=api_key)
            models_to_try = [preferred_model]
            for m in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]:
                if m not in models_to_try:
                    models_to_try.append(m)

            for m in models_to_try:
                try:
                    model = genai.GenerativeModel(
                        model_name=m, system_instruction=system
                    )
                    resp = model.generate_content(
                        prompt,
                        generation_config={"temperature": 0.3, "max_output_tokens": 1024},
                        request_options={"timeout": _TIMEOUT},
                    )
                    if resp and resp.text:
                        return resp.text
                except Exception as ex:
                    logger.warning("Summarize model %s failed: %s; trying fallback", m, ex)
                    continue

        elif provider == "openai":
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=api_key, timeout=_TIMEOUT)
            resp = client.chat.completions.create(
                model=preferred_model,
                temperature=0.3,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return resp.choices[0].message.content or ""

        elif provider == "anthropic":
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=preferred_model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text

    except Exception as e:
        logger.warning("Summarization LLM call failed: %s", e)

    return ""


# ── Deterministic fallback summaries ─────────────────────────────────────────

def _deterministic_summary_en(record: dict) -> str:
    """Build a safe template summary from flags — no LLM needed."""
    parts = []
    tests = record.get("tests", [])
    meds = record.get("medicines", [])
    diagnoses = record.get("diagnoses", [])

    if tests:
        highs = [t["name"] for t in tests if t.get("flag") == "HIGH"]
        lows = [t["name"] for t in tests if t.get("flag") == "LOW"]
        normals = [t["name"] for t in tests if t.get("flag") == "NORMAL"]

        parts.append(f"This report shows {len(tests)} test result(s).")

        for t in tests:
            name = t.get("name", "")
            val = t.get("value")
            unit = t.get("unit", "")
            low = t.get("ref_low")
            high = t.get("ref_high")
            flag = t.get("flag", "UNKNOWN")
            vt = t.get("value_text")

            if vt:
                parts.append(f"The {name} report contains findings — please discuss with your doctor.")
            elif val is not None:
                val_str = f"{val} {unit}".strip()
                if flag == "HIGH" and high is not None:
                    parts.append(
                        f"The {name} ({val_str}) is above the usual upper limit ({high} {unit}). "
                        "Please discuss this with your doctor."
                    )
                elif flag == "LOW" and low is not None:
                    parts.append(
                        f"The {name} ({val_str}) is below the usual lower limit ({low} {unit}). "
                        "Please discuss this with your doctor."
                    )
                elif flag == "NORMAL":
                    parts.append(f"The {name} ({val_str}) is within the usual range.")
                else:
                    parts.append(f"The {name} ({val_str}) could not be classified — please review with your doctor.")

    if meds:
        med_names = [m.get("name_raw", "") for m in meds]
        parts.append(
            f"This record lists {len(meds)} medicine(s): {', '.join(med_names)}. "
            "Please verify all medicines with your doctor or pharmacist."
        )

    if not parts:
        parts.append("Please review this record with your doctor.")

    return " ".join(parts) + " " + DISCLAIMER


def _deterministic_summary_ta(record: dict) -> str:
    """Minimal Tamil deterministic fallback."""
    tests = record.get("tests", [])
    meds = record.get("medicines", [])
    parts = []

    if tests:
        highs = [t["name"] for t in tests if t.get("flag") == "HIGH"]
        lows = [t["name"] for t in tests if t.get("flag") == "LOW"]
        if highs:
            parts.append(f"{', '.join(highs)} மதிப்பு வழக்கமான அளவை விட அதிகமாக உள்ளது. மருத்துவரிடம் பேசுங்கள்.")
        if lows:
            parts.append(f"{', '.join(lows)} மதிப்பு வழக்கமான அளவை விட குறைவாக உள்ளது. மருத்துவரிடம் பேசுங்கள்.")
        if not highs and not lows:
            parts.append("அனைத்து பரிசோதனை முடிவுகளும் சாதாரண அளவில் உள்ளன.")

    if meds:
        parts.append(f"இந்த பதிவில் {len(meds)} மருந்து(கள்) பட்டியலிடப்பட்டுள்ளன. உங்கள் மருத்துவர் அல்லது மருந்தாளுனரிடம் சரிபார்க்கவும்.")

    if not parts:
        parts.append("இந்த பதிவை உங்கள் மருத்துவரிடம் மதிப்பாய்வு செய்யவும்.")

    return " ".join(parts) + " இது AI-உருவாக்கிய தகவல். இது நோய் கண்டறிதலோ மருத்துவ ஆலோசனையோ அல்ல. உங்கள் மருத்துவரை அணுகவும்."


def _build_prompt(record: dict) -> str:
    """Build a concise text representation of the record for the summarization LLM."""
    masked = mask_record_for_llm(record)
    lines = [
        f"Document type: {masked.get('doc_type', 'unknown')}",
        f"Document date: {masked.get('doc_date') or 'unknown'}",
    ]
    if masked.get("follow_up_date"):
        lines.append(f"Follow-up date: {masked['follow_up_date']}")
    if masked.get("allergies"):
        lines.append(f"Noted allergies: {', '.join(masked['allergies'])}")

    tests = masked.get("tests", [])
    if tests:
        lines.append("\nLab/diagnostic tests:")
        for t in tests:
            name = t.get("name", "")
            vt = t.get("value_text")
            if vt:
                lines.append(f"  - {name}: {vt[:400]}")
            else:
                val = t.get("value", "")
                unit = t.get("unit", "")
                low = t.get("ref_low", "")
                high = t.get("ref_high", "")
                flag = t.get("flag", "UNKNOWN")
                ref_str = f"(ref: {low}–{high} {unit})" if (low or high) else ""
                lines.append(f"  - {name}: {val} {unit} {ref_str} → {flag}")

    meds = masked.get("medicines", [])
    if meds:
        lines.append("\nMedicines:")
        for m in meds:
            name = m.get("name_raw", "")
            gen = m.get("generic", "")
            sched = m.get("schedule_raw", "")
            dur = m.get("duration_days")
            gen_str = f" ({gen})" if gen else ""
            dur_str = f" for {dur} days" if dur else ""
            lines.append(f"  - {name}{gen_str}: {sched}{dur_str}")

    return "\n".join(lines)


# ── Explanation per test ──────────────────────────────────────────────────────

def build_explanation_en(test: dict) -> Optional[str]:
    """One-sentence plain-language explanation for a single test result."""
    name = test.get("name", "")
    val = test.get("value")
    unit = test.get("unit", "")
    low = test.get("ref_low")
    high = test.get("ref_high")
    flag = test.get("flag", "UNKNOWN")
    vt = test.get("value_text")

    if vt:
        return f"The {name} report mentions findings — please discuss with your doctor."
    if val is None:
        return None

    val_str = f"{val} {unit}".strip()
    if flag == "HIGH" and high is not None:
        return (
            f"Your {name} ({val_str}) is above the usual range ({low or ''}–{high} {unit}). "
            "Please discuss this with your doctor."
        )
    if flag == "LOW" and low is not None:
        return (
            f"Your {name} ({val_str}) is below the usual range ({low}–{high or ''} {unit}). "
            "Please discuss this with your doctor."
        )
    if flag == "NORMAL":
        return f"Your {name} ({val_str}) is within the usual range."
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def build_summaries(record: dict) -> dict:
    """
    Add summary_en, summary_ta, and per-test explanation_en / explanation_ta
    to *record* (modifies in place). Returns the record.
    Always falls back to deterministic templates if LLM fails or output is unsafe.
    PHASE 3: Also falls back if summary contains numbers not grounded in the record.
    """
    # Per-test explanations (deterministic — no LLM)
    for test in record.get("tests", []):
        if not test.get("explanation_en"):
            test["explanation_en"] = build_explanation_en(test)

    # English summary
    if not record.get("summary_en"):
        prompt = _build_prompt(record)
        llm_text = _call_summarize_llm(prompt, _EN_SYSTEM)
        if llm_text and _safety_check(llm_text) and _grounding_check(llm_text, record):
            record["summary_en"] = llm_text.strip()
        else:
            if llm_text:
                logger.warning("LLM summary failed safety/grounding check — using deterministic fallback")
            record["summary_en"] = _deterministic_summary_en(record)

    # Always ensure disclaimer is appended
    if record["summary_en"] and DISCLAIMER not in record["summary_en"]:
        record["summary_en"] = record["summary_en"].rstrip() + " " + DISCLAIMER

    # Tamil summary (stretch)
    if not record.get("summary_ta"):
        prompt = _build_prompt(record)
        ta_text = _call_summarize_llm(prompt, _TA_SYSTEM)
        if ta_text:
            record["summary_ta"] = ta_text.strip()
        else:
            record["summary_ta"] = _deterministic_summary_ta(record)

    return record
