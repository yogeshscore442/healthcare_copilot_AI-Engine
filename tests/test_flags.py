"""
test_flags.py — Unit tests for deterministic flag computation.
Run: pytest tests/test_flags.py -v
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.flags import compute_flag, lookup_reference, get_loinc


class TestComputeFlag:
    # ── HbA1c ─────────────────────────────────────────────────────────────────
    def test_hba1c_high(self):
        assert compute_flag("HbA1c", 7.8, "%", None, None) == "HIGH"

    def test_hba1c_normal(self):
        assert compute_flag("HbA1c", 5.2, "%", None, None) == "NORMAL"

    def test_hba1c_low(self):
        assert compute_flag("HbA1c", 3.5, "%", None, None) == "LOW"

    # ── Fasting Glucose ───────────────────────────────────────────────────────
    def test_fbs_high(self):
        assert compute_flag("Fasting Blood Glucose", 142, "mg/dL", None, None) == "HIGH"

    def test_fbs_normal(self):
        assert compute_flag("FBS", 88, "mg/dL", None, None) == "NORMAL"

    def test_fbs_low(self):
        assert compute_flag("FBS", 55, "mg/dL", None, None) == "LOW"

    # ── Haemoglobin ───────────────────────────────────────────────────────────
    def test_hb_female_low(self):
        # Uses male range by default (first match); document range takes priority
        # With document range provided:
        assert compute_flag("Haemoglobin", 10.2, "g/dL", 12.0, 16.0) == "LOW"

    def test_hb_normal_with_doc_range(self):
        assert compute_flag("Hb", 14.5, "g/dL", 13.5, 17.5) == "NORMAL"

    # ── Cholesterol ───────────────────────────────────────────────────────────
    def test_ldl_high(self):
        assert compute_flag("LDL Cholesterol", 135, "mg/dL", None, None) == "HIGH"

    def test_ldl_normal(self):
        assert compute_flag("LDL", 90, "mg/dL", None, None) == "NORMAL"

    def test_total_chol_high(self):
        assert compute_flag("Total Cholesterol", 220, "mg/dL", None, None) == "HIGH"

    # ── TSH ──────────────────────────────────────────────────────────────────
    def test_tsh_high(self):
        assert compute_flag("TSH", 6.5, "mIU/L", None, None) == "HIGH"

    def test_tsh_low(self):
        assert compute_flag("TSH", 0.1, "mIU/L", None, None) == "LOW"

    def test_tsh_normal(self):
        assert compute_flag("Thyroid Stimulating Hormone", 2.1, "mIU/L", None, None) == "NORMAL"

    # ── Creatinine ───────────────────────────────────────────────────────────
    def test_creatinine_high(self):
        assert compute_flag("Serum Creatinine", 1.8, "mg/dL", None, None) == "HIGH"

    # ── WBC ──────────────────────────────────────────────────────────────────
    def test_wbc_normal(self):
        assert compute_flag("WBC", 7.2, "10³/µL", None, None) == "NORMAL"

    def test_wbc_high(self):
        assert compute_flag("Total WBC", 13.0, "10³/µL", None, None) == "HIGH"

    # ── Edge cases ────────────────────────────────────────────────────────────
    def test_none_value_returns_unknown(self):
        assert compute_flag("HbA1c", None, "%", None, None) == "UNKNOWN"

    def test_unknown_test_returns_unknown(self):
        assert compute_flag("FictionalBiomarker", 100, "units", None, None) == "UNKNOWN"

    def test_document_range_overrides_table(self):
        # Custom range: 5-8 → 7.8 is NORMAL (not HIGH per standard range)
        assert compute_flag("HbA1c", 7.8, "%", 5.0, 8.0) == "NORMAL"

    def test_only_upper_bound(self):
        # LDL has no lower bound
        assert compute_flag("LDL", 80, "mg/dL", None, 100) == "NORMAL"
        assert compute_flag("LDL", 110, "mg/dL", None, 100) == "HIGH"

    def test_alias_lookup(self):
        # "A1c" should resolve to HbA1c entry
        assert compute_flag("A1c", 8.0, "%", None, None) == "HIGH"


class TestLoinc:
    def test_hba1c_loinc(self):
        assert get_loinc("HbA1c") == "4548-4"

    def test_wbc_loinc(self):
        assert get_loinc("WBC") == "6690-2"

    def test_unknown_returns_none(self):
        assert get_loinc("NonExistentTest") is None
