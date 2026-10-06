"""
extract.py — LLM-powered medical document extraction.

Supports providers: google | openai | anthropic
All credentials come from environment variables — never hardcoded.
Retries once on validation failure, returns error record on all other failures.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Optional

from .models import DISCLAIMER, HealthRecord, make_error_record
from .ocr import encode_image_b64, load_document
from .privacy import mask_text
from .flags import compute_flag, get_loinc
from .brands import normalize_brand
from .dosage import parse_schedule
from .diagnoses import lookup_icd10

logger = logging.getLogger(__name__)

def _get_api_key() -> str:
    return os.getenv("LLM_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

def _get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "google").lower()

def _get_model() -> str:
    return os.getenv("LLM_MODEL") or "gemini-2.5-pro"

_TIMEOUT = 45          # seconds per LLM call
_MAX_RETRIES = 2       # total attempts (initial + 1 retry)

# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a medical document extraction assistant.
Extract structured information from the provided medical document image (and optional OCR text for context).

STRICT RULES — violating any rule disqualifies the output:
1. Extract ONLY what is explicitly visible in the document. Never infer, guess, or add outside knowledge.
2. If a field value is unclear or absent → use null. Never fabricate values.
3. Return ONLY valid JSON. No markdown fences, no prose, no explanations.
4. Include a confidence score (0.0–1.0) for every medicine and test entry.
5. Include normalized bbox [x, y, w, h] (0.0–1.0 relative to page dimensions) when the item is clearly locatable; else null.
6. Do NOT add diagnoses, drug interactions, or clinical interpretations — extract only what is written.
7. For diagnostic reports (X-ray, ECG, ultrasound), put the findings + impression text verbatim in value_text; set value=null.
8. Dates must be YYYY-MM-DD or null.
9. doc_type must be one of: prescription, lab_report, discharge_summary, diagnostic_report.
10. language must be one of: en, ta, mixed.

Output JSON structure (all fields required; use null or [] when absent):
{
  "doc_type": "...",
  "doc_date": "YYYY-MM-DD or null",
  "collection_date": "YYYY-MM-DD or null",
  "follow_up_date": "YYYY-MM-DD or null",
  "language": "en|ta|mixed",
  "patient_name_present": true|false,
  "allergies": [],
  "medicines": [
    {
      "name_raw": "string",
      "generic": "string or null",
      "strength": "string or null",
      "schedule_raw": "string or null",
      "schedule_parsed": [],
      "food_instruction": "before_food|after_food|null",
      "duration_days": number|null,
      "confidence": 0.0-1.0,
      "bbox": [x,y,w,h]|null
    }
  ],
  "tests": [
    {
      "name": "string",
      "loinc": "string or null",
      "value": number|null,
      "value_text": "string or null",
      "unit": "string or null",
      "ref_low": number|null,
      "ref_high": number|null,
      "flag": "UNKNOWN",
      "explanation_en": null,
      "explanation_ta": null,
      "confidence": 0.0-1.0,
      "bbox": [x,y,w,h]|null
    }
  ],
  "diagnoses": [
    {"text": "string", "confidence": 0.0-1.0}
  ]
}"""

# ── Doc-type-specific prompt addenda (PHASE 2) ───────────────────────────────────

_PRESCRIPTION_ADDENDUM = """
This document is a PRESCRIPTION. Extra rules:
- medicines[] must be exhaustive; each row on the prescription is one entry.
- Extract schedule_raw EXACTLY as written (e.g. "1-0-1", "BD", "TDS after food").
- Capture duration_days if the number of days is stated (e.g. "5 days", "1 week" → 7).
- food_instruction: set to before_food or after_food only if explicitly stated.
- tests[] should almost always be empty for a prescription.
- diagnoses[] may list the reason for visit if printed on the form."""

_LAB_ADDENDUM = """
This document is a LAB REPORT. Extra rules:
- tests[] must be exhaustive; capture every row in the results table.
- For each test: extract name, value (numeric), unit, ref_low, ref_high from the printed reference range column.
- If reference range is printed as e.g. "4.0–6.0" parse ref_low=4.0 and ref_high=6.0.
- Do NOT compute flag; always output flag="UNKNOWN".
- collection_date is the specimen collection date (often different from the report date).
- medicines[] and diagnoses[] are usually empty for a pure lab report."""

_DISCHARGE_ADDENDUM = """
This document is a DISCHARGE SUMMARY. Extra rules:
- Extract medicines[] from the "discharge medications" or "at-discharge" section only.
- tests[] should list key investigations mentioned with numeric values.
- diagnoses[] should list primary and secondary diagnoses verbatim.
- doc_date is the discharge date; collection_date is null unless explicitly stated.
- follow_up_date should be extracted if a review appointment is mentioned."""

_DIAGNOSTIC_ADDENDUM = """
This document is a DIAGNOSTIC/IMAGING REPORT (X-ray, ECG, Ultrasound, MRI, etc.). Extra rules:
- tests[] should each represent one finding/measurement with value_text = verbatim impression.
- Do NOT extract numeric values unless they are explicit measurements (e.g. "EF 55%").
- medicines[] and diagnoses[] are usually empty.
- The "Impression" or "Conclusion" section text goes into value_text of the primary test entry."""

_DOC_TYPE_ADDENDA = {
    "prescription": _PRESCRIPTION_ADDENDUM,
    "lab_report": _LAB_ADDENDUM,
    "discharge_summary": _DISCHARGE_ADDENDUM,
    "diagnostic_report": _DIAGNOSTIC_ADDENDUM,
}

def _classify_doc_type_from_text(ocr_text: str) -> str:
    """
    Lightweight heuristic to pre-classify doc type from OCR text.
    Returns one of: prescription | lab_report | discharge_summary | diagnostic_report | unknown
    Used to select the doc-type-specific prompt addendum before the LLM call.
    """
    if not ocr_text:
        return "unknown"
    text = ocr_text.lower()

    lab_signals = [
        "haemoglobin", "hemoglobin", "hba1c", "fasting glucose", "creatinine",
        "urea", "wbc", "rbc", "platelet", "triglyceride", "cholesterol",
        "reference range", "normal range", "test result", "specimen", "lab id",
        "collection date", "sample type",
    ]
    rx_signals = [
        "rx", "prescription", "sig:", "dispense", "refills", "take",
        "tablet", "capsule", "syrup", "1-0-1", "0-0-1", "bd", "tds", "od",
        "after food", "before food", "twice daily", "once daily",
    ]
    discharge_signals = [
        "discharge summary", "discharge date", "admission date",
        "final diagnosis", "discharge medications", "course in hospital",
        "condition at discharge",
    ]
    diagnostic_signals = [
        "impression", "x-ray", "xray", "ultrasound", "mri", "ct scan",
        "ecg", "echo", "sonography", "radiograph", "finding", "conclusion",
    ]

    scores = {
        "lab_report": sum(1 for s in lab_signals if s in text),
        "prescription": sum(1 for s in rx_signals if s in text),
        "discharge_summary": sum(1 for s in discharge_signals if s in text),
        "diagnostic_report": sum(1 for s in diagnostic_signals if s in text),
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] >= 2 else "unknown"


def _get_typed_system_prompt(doc_type_hint: str) -> str:
    """Return the system prompt + doc-type-specific addendum."""
    addendum = _DOC_TYPE_ADDENDA.get(doc_type_hint, "")
    return (_SYSTEM_PROMPT + addendum) if addendum else _SYSTEM_PROMPT


def _user_message(b64_image: str, fallback_text: str, lang_hint: str) -> str:
    hint = f"Language hint: {lang_hint}. " if lang_hint != "auto" else ""
    ocr = mask_text(fallback_text[:3000]) if fallback_text else "(no OCR text available)"
    return (
        f"{hint}Please extract all information from this medical document.\n\n"
        f"OCR context text (may have errors):\n{ocr}"
    )


# ── Provider dispatch ─────────────────────────────────────────────────────────

def _call_google(b64_image: str, user_msg: str, system_prompt: str | None = None) -> str:
    import google.generativeai as genai  # type: ignore
    from google.generativeai.types import HarmCategory, HarmBlockThreshold  # type: ignore
    import base64

    api_key = _get_api_key()
    if not api_key:
        raise ValueError("Google API key is not configured. Set LLM_API_KEY or GOOGLE_API_KEY in .env")

    genai.configure(api_key=api_key)
    preferred_model = _get_model()
    models_to_try = [preferred_model]
    for m in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]:
        if m not in models_to_try:
            models_to_try.append(m)

    image_bytes = base64.b64decode(b64_image)
    prompt = system_prompt or _SYSTEM_PROMPT
    last_err = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=prompt,
            )
            response = model.generate_content(
                [
                    {"mime_type": "image/jpeg", "data": image_bytes},
                    user_msg,
                ],
                generation_config={"temperature": 0.0, "max_output_tokens": 4096},
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
                request_options={"timeout": _TIMEOUT},
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            logger.warning("Gemini model %s failed: %s; trying next fallback", model_name, e)
            continue

    raise last_err or RuntimeError("All candidate Gemini models failed")


def _call_openai(b64_image: str, user_msg: str) -> str:
    from openai import OpenAI  # type: ignore
    api_key = _get_api_key()
    model = _get_model()

    client = OpenAI(api_key=api_key, timeout=_TIMEOUT)
    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                    {"type": "text", "text": user_msg},
                ],
            },
        ],
    )
    return response.choices[0].message.content or ""


def _call_anthropic(b64_image: str, user_msg: str) -> str:
    import anthropic  # type: ignore
    api_key = _get_api_key()
    model = _get_model()

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image,
                        },
                    },
                    {"type": "text", "text": user_msg},
                ],
            }
        ],
    )
    return response.content[0].text


_PROVIDER_MAP = {
    "google": _call_google,
    "openai": _call_openai,
    "anthropic": _call_anthropic,
}


def _call_llm(b64_image: str, user_msg: str, system_prompt: str | None = None) -> str:
    """Call the configured LLM provider with retry on transient errors."""
    provider = _get_provider()
    caller = _PROVIDER_MAP.get(provider)
    if not caller:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Set to google|openai|anthropic")

    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES):
        try:
            # Pass system_prompt only to providers that accept it; others ignore extra kwargs gracefully
            if provider == "google":
                return caller(b64_image, user_msg, system_prompt)
            return caller(b64_image, user_msg)
        except Exception as e:
            last_exc = e
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            if code == 429:
                wait = 2 ** attempt
                logger.warning("Rate limited — waiting %ds (attempt %d)", wait, attempt + 1)
                time.sleep(wait)
            else:
                logger.warning("LLM call failed attempt %d: %s", attempt + 1, e)
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(1)

    raise last_exc or RuntimeError("LLM call failed after retries")


# ── JSON extraction ───────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extract and parse JSON object from LLM response string."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        if text.endswith("```"):
            text = text[:-3]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")
    clean_text = text[start:end].strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        fixed = re.sub(r",\s*([\]}])", r"\1", clean_text)
        return json.loads(fixed)


# ── Post-processing ───────────────────────────────────────────────────────────

def _apply_flags_and_enrichment(data: dict) -> dict:
    """
    Apply deterministic flags + brand normalisation + dosage parsing + ICD-10
    to the raw LLM-extracted dict. Modifies in-place, returns dict.
    """
    # Tests — compute flags in code
    for i, test in enumerate(data.get("tests", [])):
        flag = compute_flag(
            test_name=test.get("name", ""),
            value=test.get("value"),
            unit=test.get("unit"),
            ref_low=test.get("ref_low"),
            ref_high=test.get("ref_high"),
        )
        test["flag"] = flag
        # Fill LOINC if missing
        if not test.get("loinc"):
            test["loinc"] = get_loinc(test.get("name", ""))

    # Medicines — brand normalisation + dosage parsing
    for med in data.get("medicines", []):
        # Brand → generic (only if generic is null)
        if not med.get("generic"):
            generic, strength = normalize_brand(med.get("name_raw", ""))
            if generic:
                med["generic"] = generic
            if strength and not med.get("strength"):
                med["strength"] = strength

        # Dosage parsing (override LLM with deterministic parser)
        slots, food, dur = parse_schedule(med.get("schedule_raw"))
        med["schedule_parsed"] = slots
        if food:
            med["food_instruction"] = food
        if dur and not med.get("duration_days"):
            med["duration_days"] = dur

    # Diagnoses — map ICD-10 codes
    for diag in data.get("diagnoses", []):
        if not diag.get("icd10"):
            matched = lookup_icd10(diag.get("text", ""))
            if matched:
                diag["icd10"] = matched[0]

    return data


def _compute_needs_review(data: dict) -> list[str]:
    """Return JSON-path strings for fields with confidence < 0.7 or missing critical data."""
    needs = []
    for i, med in enumerate(data.get("medicines", [])):
        if med.get("confidence", 1.0) < 0.7:
            needs.append(f"medicines[{i}]")
    for i, test in enumerate(data.get("tests", [])):
        if test.get("confidence", 1.0) < 0.7:
            needs.append(f"tests[{i}]")
        if test.get("flag") == "UNKNOWN" and test.get("value") is not None:
            needs.append(f"tests[{i}]")
    return list(dict.fromkeys(needs))  # deduplicate preserving order


def _fallback_extract_from_text(text: str, record_id: str) -> Optional[dict]:
    """Deterministic fallback parser: extracts tests and medicines from OCR text directly."""
    if not text or len(text.strip()) < 10:
        return None

    from .flags import _load as _load_ranges
    from .brands import _load as _load_brands

    ranges = _load_ranges()
    brands = _load_brands()

    extracted_tests = []
    lines = text.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        line_lower = line_clean.lower()
        for test_key, entry in ranges.items():
            for alias in entry.get("aliases", []):
                if re.search(r"\b" + re.escape(alias) + r"\b", line_lower):
                    match = re.search(r"\b(\d+(?:\.\d+)?)\b", line_clean)
                    if match:
                        try:
                            val = float(match.group(1))
                            extracted_tests.append({
                                "name": alias.title(),
                                "loinc": entry.get("loinc"),
                                "value": val,
                                "value_text": None,
                                "unit": entry.get("unit"),
                                "ref_low": entry.get("ref_low"),
                                "ref_high": entry.get("ref_high"),
                                "flag": "UNKNOWN",
                                "explanation_en": None,
                                "explanation_ta": None,
                                "confidence": 0.80,
                                "bbox": None,
                            })
                            break
                        except ValueError:
                            pass

    extracted_meds = []
    for line in lines:
        line_clean = line.strip()
        for brand, (generic, strength) in brands.items():
            if re.search(r"\b" + re.escape(brand.lower()) + r"\b", line_clean.lower()):
                slots, food, dur = parse_schedule(line_clean)
                extracted_meds.append({
                    "name_raw": brand,
                    "generic": generic,
                    "strength": strength,
                    "schedule_raw": line_clean,
                    "schedule_parsed": slots,
                    "food_instruction": food,
                    "duration_days": dur,
                    "confidence": 0.85,
                    "bbox": None,
                })
                break

    if not extracted_tests and not extracted_meds:
        return None

    if extracted_meds and not extracted_tests:
        doc_type = "prescription"
    elif extracted_tests and not extracted_meds:
        doc_type = "lab_report"
    else:
        doc_type = "discharge_summary"

    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    doc_date = date_match.group(1) if date_match else None

    return {
        "record_id": record_id,
        "doc_type": doc_type,
        "doc_date": doc_date,
        "collection_date": None,
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": False,
        "allergies": [],
        "medicines": extracted_meds,
        "tests": extracted_tests,
        "diagnoses": [],
        "summary_en": None,
        "summary_ta": None,
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None,
    }


# ── Public extract function ───────────────────────────────────────────────────

def extract_from_file(file_path: str, mime: str, lang_hint: str = "auto") -> dict:
    """
    Core extraction function. Never raises — returns error record on all failures.
    """
    record_id = str(uuid.uuid4())

    # ── 1. Load document ──────────────────────────────────────────────────────
    doc = load_document(file_path, mime)
    if doc["error"] and not doc["pages"]:
        return make_error_record(
            "LOAD_FAILED",
            f"Could not load document: {doc['error']}",
        )

    if not doc["pages"]:
        # Tesseract-only fallback (e.g. poppler missing for PDF)
        if not doc["fallback_text"]:
            return make_error_record("NO_CONTENT", "Document has no readable content.")
        b64 = ""
    else:
        b64 = encode_image_b64(doc["pages"][0])

    # PHASE 2: pre-classify from OCR text to choose a focused prompt
    doc_type_hint = _classify_doc_type_from_text(doc.get("fallback_text", ""))
    typed_system_prompt = _get_typed_system_prompt(doc_type_hint)
    logger.debug("Pre-classification hint: %s", doc_type_hint)

    user_msg = _user_message(b64, doc["fallback_text"], lang_hint)

    # ── 2. LLM extraction with retry on validation failure ────────────────────
    raw_data: Optional[dict] = None
    validation_error: str = ""

    for attempt in range(_MAX_RETRIES):
        try:
            if not b64 and not _get_provider():
                raise ValueError("No image and no LLM provider configured.")

            if b64:
                llm_text = _call_llm(
                    b64,
                    user_msg if attempt == 0 else
                    user_msg + f"\n\nPrevious attempt failed validation: {validation_error}. Fix and return valid JSON only.",
                    typed_system_prompt,
                )
            else:
                llm_text = "{}"

            raw_data = _extract_json(llm_text)
            # Validate with Pydantic
            raw_data["record_id"] = record_id
            raw_data["disclaimer"] = DISCLAIMER
            raw_data.setdefault("needs_review", [])
            raw_data.setdefault("summary_en", None)
            raw_data.setdefault("summary_ta", None)
            raw_data.setdefault("error", None)
            raw_data.setdefault("allergies", [])
            raw_data.setdefault("collection_date", None)
            raw_data.setdefault("follow_up_date", None)

            validated = HealthRecord.model_validate(raw_data)
            raw_data = validated.model_dump()
            break  # success

        except Exception as e:
            validation_error = str(e)
            logger.warning("Extraction attempt %d failed: %s", attempt + 1, e)
            raw_data = None

    if raw_data is None:
        if doc.get("fallback_text"):
            raw_data = _fallback_extract_from_text(doc["fallback_text"], record_id)
        if raw_data is None:
            return make_error_record(
                "EXTRACTION_FAILED",
                f"Could not extract valid data after {_MAX_RETRIES} attempts.",
            )

    # ── 3. Deterministic post-processing ─────────────────────────────────────
    raw_data = _apply_flags_and_enrichment(raw_data)
    raw_data["needs_review"] = _compute_needs_review(raw_data)

    return raw_data
