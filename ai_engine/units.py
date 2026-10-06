"""
units.py — Authoritative clinical unit conversion constants and logic.
All factors should be verified against trusted laboratory standards (e.g. IFCC, CDC, Tietz Clinical Guide).
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# NOTE: verify against a trusted source (e.g., IFCC / CDC / Tietz Textbook of Clinical Chemistry).
# Standard Molecular Weights / Clinical Conversion Constants:
# - Glucose (C6H12O6, MW 180.16 g/mol): 1 mmol/L = 18.0182 mg/dL
# - Cholesterol (Total, LDL, HDL, MW 386.65 g/mol): 1 mmol/L = 38.67 mg/dL
# - Triglycerides (Triolein basis, MW 885.4 g/mol): 1 mmol/L = 88.57 mg/dL
# - Creatinine (C4H7N3O, MW 113.12 g/mol): 1 mg/dL = 88.4 umol/L (µmol/L)
# - Haemoglobin: 1 g/dL = 10.0 g/L

CONVERSION_FACTORS = {
    # (canonical_test_category, from_unit, to_unit): multiplier (from * multiplier = to)
    ("glucose", "mmol/l", "mg/dl"): 18.0182,
    ("glucose", "mg/dl", "mmol/l"): 1.0 / 18.0182,

    ("cholesterol", "mmol/l", "mg/dl"): 38.67,
    ("cholesterol", "mg/dl", "mmol/l"): 1.0 / 38.67,

    ("triglycerides", "mmol/l", "mg/dl"): 88.57,
    ("triglycerides", "mg/dl", "mmol/l"): 1.0 / 88.57,

    ("creatinine", "mg/dl", "umol/l"): 88.4,
    ("creatinine", "umol/l", "mg/dl"): 1.0 / 88.4,
    ("creatinine", "mg/dl", "µmol/l"): 88.4,
    ("creatinine", "µmol/l", "mg/dl"): 1.0 / 88.4,

    ("haemoglobin", "g/dl", "g/l"): 10.0,
    ("haemoglobin", "g/l", "g/dl"): 0.1,
}


def _norm_unit(unit: str) -> str:
    """Normalize unit string for standard lookup."""
    u = unit.lower().strip()
    u = re.sub(r"\s+", "", u)
    u = u.replace("gm/dl", "g/dl").replace("gm%", "g/dl").replace("gm/l", "g/l")
    u = u.replace("micro", "u").replace("µ", "u")
    return u


def _get_category(test_name: str) -> Optional[str]:
    """Identify category for unit conversion."""
    t = test_name.lower().strip()
    if "glucose" in t or "sugar" in t or "fbs" in t or "ppbs" in t or "rbs" in t:
        return "glucose"
    if "cholesterol" in t or "ldl" in t or "hdl" in t:
        return "cholesterol"
    if "triglyceride" in t or "tg" in t:
        return "triglycerides"
    if "creatinine" in t:
        return "creatinine"
    if "haemoglobin" in t or "hemoglobin" in t or "hb" in t:
        return "haemoglobin"
    return None


def can_convert_unit(from_unit: str, to_unit: str, test_name: str) -> bool:
    """Check if conversion factor exists for given test and units."""
    cat = _get_category(test_name)
    if not cat:
        return False
    u1 = _norm_unit(from_unit)
    u2 = _norm_unit(to_unit)
    if u1 == u2:
        return True
    return (cat, u1, u2) in CONVERSION_FACTORS


def convert_value(val: float, from_unit: str, to_unit: str, test_name: str) -> Optional[float]:
    """
    Convert numerical value between units.
    Returns None if unsupported.
    """
    if val is None:
        return None
    u1 = _norm_unit(from_unit)
    u2 = _norm_unit(to_unit)
    if u1 == u2:
        return val

    cat = _get_category(test_name)
    if not cat:
        return None

    factor = CONVERSION_FACTORS.get((cat, u1, u2))
    if factor is not None:
        return round(val * factor, 3)

    return None


def convert_range_to_doc_unit(ref_low: Optional[float], ref_high: Optional[float], table_unit: str, doc_unit: str, test_name: str) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Converts default reference range bounds to match document unit.
    Returns (converted_low, converted_high, is_success).
    If cannot convert, returns (ref_low, ref_high, False).
    """
    u_tab = _norm_unit(table_unit)
    u_doc = _norm_unit(doc_unit)
    if u_tab == u_doc:
        return ref_low, ref_high, True

    cat = _get_category(test_name)
    if not cat:
        return ref_low, ref_high, False

    factor = CONVERSION_FACTORS.get((cat, u_tab, u_doc))
    if factor is None:
        return ref_low, ref_high, False

    new_low = round(ref_low * factor, 2) if ref_low is not None else None
    new_high = round(ref_high * factor, 2) if ref_high is not None else None
    return new_low, new_high, True
