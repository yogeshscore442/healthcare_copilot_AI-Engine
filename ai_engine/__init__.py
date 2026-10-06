"""
ai_engine — Public interface for the AI Health Copilot extraction engine.

Usage:
    from ai_engine import extract_record
    result = extract_record("samples/lab1.jpg", "image/jpeg")

extract_record() NEVER raises. On any failure it returns a contract-valid
error dict with error={"code": ..., "message": ...}.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # load .env at import time

from .cache import get_cached, set_cached
from .extract import extract_from_file
from .models import make_error_record, DISCLAIMER
from .summarize import build_summaries
from .interactions import check_drug_interactions, get_drug_advisories
from .affordability import calculate_prescription_savings
from .fhir import record_to_fhir_bundle, export_fhir_json
from .voice import generate_audio, get_browser_speech_html

logger = logging.getLogger(__name__)

__all__ = [
    "extract_record",
    "calculate_prescription_savings",
    "record_to_fhir_bundle",
    "export_fhir_json",
    "check_drug_interactions",
    "get_drug_advisories",
    "generate_audio",
    "get_browser_speech_html",
]
__version__ = "0.3.0"


def extract_record(
    file_path: str,
    mime: str,
    lang_hint: str = "auto",
) -> dict:
    """
    Extract a contract-compliant record dict from a medical document.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the document file (image or PDF).
    mime : str
        MIME type, e.g. "image/jpeg", "image/png", "application/pdf".
    lang_hint : str
        Language hint: "auto" | "en" | "ta". Used to guide Tamil extraction.

    Returns
    -------
    dict
        Contract-compliant record. Always present: record_id, disclaimer, error.
        On success: error=null. On failure: error={"code", "message"}.

    Guarantee
    ---------
    This function NEVER raises an exception. All errors are caught and returned
    in the contract error field.
    """
    try:
        # ── Mock mode ────────────────────────────────────────────────────────
        if os.getenv("USE_MOCK_AI", "false").lower() == "true":
            return _load_mock(mime, file_path)

        # ── Cache check ──────────────────────────────────────────────────────
        cached = get_cached(file_path)
        if cached is not None:
            # Ensure additive fields (summary_hi, safety_alerts, cost_savings) are populated
            if not cached.get("summary_hi"):
                cached = build_summaries(cached)
            if "safety_alerts" not in cached and cached.get("medicines"):
                try:
                    cached["safety_alerts"] = check_drug_interactions(cached["medicines"])
                    cached["drug_advisories"] = get_drug_advisories(cached["medicines"])
                except Exception:
                    pass
            if "cost_savings" not in cached and cached.get("medicines"):
                try:
                    cached["cost_savings"] = calculate_prescription_savings(cached["medicines"])
                except Exception:
                    pass
            return cached

        # ── Extract ──────────────────────────────────────────────────────────
        record = extract_from_file(file_path, mime, lang_hint)

        if record.get("error"):
            return record  # skip summary on extraction error

        # ── Summarize ────────────────────────────────────────────────────────
        record = build_summaries(record)

        # ── Clinical Drug Safety & Advisories ────────────────────────────────
        if record.get("medicines"):
            try:
                record["safety_alerts"] = check_drug_interactions(record["medicines"])
                record["drug_advisories"] = get_drug_advisories(record["medicines"])
            except Exception as e:
                logger.warning("Safety alerts check skipped: %s", e)
                record["safety_alerts"] = []
                record["drug_advisories"] = []
            
            try:
                record["cost_savings"] = calculate_prescription_savings(record["medicines"])
            except Exception as e:
                logger.warning("Cost savings calculation skipped: %s", e)
                record["cost_savings"] = None
        else:
            record["safety_alerts"] = []
            record["drug_advisories"] = []
            record["cost_savings"] = None

        # ── Cache result ─────────────────────────────────────────────────────
        set_cached(file_path, record)

        return record

    except Exception as e:
        logger.exception("Unexpected error in extract_record for %s", file_path)
        return make_error_record(
            "UNEXPECTED_ERROR",
            f"An unexpected error occurred: {type(e).__name__}: {e}",
        )


# ── Mock helper ───────────────────────────────────────────────────────────────

def _load_mock(mime: str, file_path: str) -> dict:
    """Return appropriate mock JSON based on mime type or file name hint."""
    import json
    from pathlib import Path

    root = Path(__file__).parent.parent / "contract"
    name_lower = file_path.lower()

    if "prescription" in name_lower or "rx" in name_lower:
        mock_file = root / "mock_prescription.json"
    elif "discharge" in name_lower:
        mock_file = root / "mock_discharge_summary.json"
    elif "diagnostic" in name_lower or "xray" in name_lower or "ecg" in name_lower:
        mock_file = root / "mock_diagnostic_report.json"
    else:
        mock_file = root / "mock_lab_report.json"

    try:
        with open(mock_file, encoding="utf-8") as f:
            data = json.load(f)
        import uuid
        data["record_id"] = str(uuid.uuid4())  # fresh ID each call
        if data.get("medicines"):
            try:
                data["safety_alerts"] = check_drug_interactions(data["medicines"])
                data["drug_advisories"] = get_drug_advisories(data["medicines"])
                data["cost_savings"] = calculate_prescription_savings(data["medicines"])
            except Exception:
                pass
        logger.info("USE_MOCK_AI=true — returning %s", mock_file.name)
        return data
    except Exception as e:
        return make_error_record("MOCK_LOAD_FAILED", f"Could not load mock file: {e}")
