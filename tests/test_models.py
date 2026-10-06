"""
test_models.py — Unit tests for Pydantic contract models.
Run: pytest tests/test_models.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.models import (
    DISCLAIMER,
    DiagnosisRecord,
    HealthRecord,
    MedicineRecord,
    TestRecord,
    make_error_record,
)


class TestMedicineRecord:
    def test_valid_medicine(self):
        med = MedicineRecord(
            name_raw="Tab Dolo 650",
            generic="Paracetamol",
            strength="650 mg",
            schedule_raw="1-0-1",
            schedule_parsed=["morning", "night"],
            food_instruction=None,
            duration_days=5,
            confidence=0.95,
            bbox=[0.1, 0.2, 0.8, 0.05],
        )
        assert med.generic == "Paracetamol"
        assert med.confidence == 0.95

    def test_bbox_must_be_4_elements(self):
        with pytest.raises(Exception):
            MedicineRecord(name_raw="X", confidence=0.9, bbox=[0.1, 0.2])

    def test_confidence_clamped_schema(self):
        with pytest.raises(Exception):
            MedicineRecord(name_raw="X", confidence=1.5)

    def test_duration_must_be_positive(self):
        with pytest.raises(Exception):
            MedicineRecord(name_raw="X", confidence=0.9, duration_days=-1)

    def test_null_generic_allowed(self):
        med = MedicineRecord(name_raw="Unknown Brand", confidence=0.6)
        assert med.generic is None


class TestTestRecord:
    def test_valid_test(self):
        t = TestRecord(
            name="HbA1c",
            loinc="4548-4",
            value=7.8,
            unit="%",
            ref_low=4.0,
            ref_high=5.6,
            flag="HIGH",
            confidence=0.95,
        )
        assert t.flag == "HIGH"

    def test_flag_default_unknown(self):
        t = TestRecord(name="SomeTest", confidence=0.8)
        assert t.flag == "UNKNOWN"

    def test_invalid_flag_rejected(self):
        with pytest.raises(Exception):
            TestRecord(name="SomeTest", confidence=0.8, flag="BORDERLINE")

    def test_value_text_allowed(self):
        t = TestRecord(
            name="Chest X-Ray",
            value_text="No consolidation seen.",
            confidence=0.9,
        )
        assert t.value_text == "No consolidation seen."
        assert t.value is None


class TestHealthRecord:
    def _minimal(self) -> dict:
        return {
            "doc_type": "lab_report",
            "disclaimer": DISCLAIMER,
        }

    def test_valid_record(self):
        r = HealthRecord(**self._minimal())
        assert r.doc_type == "lab_report"
        assert r.disclaimer == DISCLAIMER
        assert r.record_id  # auto-generated UUID

    def test_disclaimer_always_fixed(self):
        r = HealthRecord(doc_type="prescription", disclaimer="something else")
        assert r.disclaimer == DISCLAIMER

    def test_date_format_valid(self):
        r = HealthRecord(doc_type="lab_report", doc_date="2024-09-15")
        assert r.doc_date == "2024-09-15"

    def test_date_format_invalid(self):
        with pytest.raises(Exception):
            HealthRecord(doc_type="lab_report", doc_date="15-09-2024")

    def test_date_null_allowed(self):
        r = HealthRecord(doc_type="lab_report", doc_date=None)
        assert r.doc_date is None

    def test_doc_type_enum(self):
        with pytest.raises(Exception):
            HealthRecord(doc_type="unknown_type")

    def test_needs_review_dedup(self):
        r = HealthRecord(doc_type="lab_report")
        r.mark_review("tests[0]")
        r.mark_review("tests[0]")
        assert r.needs_review.count("tests[0]") == 1

    def test_empty_lists_default(self):
        r = HealthRecord(doc_type="prescription")
        assert r.medicines == []
        assert r.tests == []
        assert r.diagnoses == []
        assert r.allergies == []

    def test_full_record_validates(self):
        r = HealthRecord(
            doc_type="prescription",
            doc_date="2024-09-20",
            language="en",
            patient_name_present=True,
            medicines=[
                {
                    "name_raw": "Dolo 650",
                    "confidence": 0.95,
                    "schedule_parsed": ["morning", "night"],
                }
            ],
            tests=[],
            diagnoses=[{"text": "Fever", "confidence": 0.8}],
            needs_review=[],
            summary_en="Test summary.",
            disclaimer=DISCLAIMER,
        )
        assert len(r.medicines) == 1
        assert len(r.diagnoses) == 1


class TestMakeErrorRecord:
    def test_returns_dict(self):
        result = make_error_record("TEST_ERROR", "Something went wrong")
        assert isinstance(result, dict)

    def test_error_field_present(self):
        result = make_error_record("TEST_ERROR", "Something went wrong")
        assert result["error"]["code"] == "TEST_ERROR"
        assert "Something went wrong" in result["error"]["message"]

    def test_disclaimer_present(self):
        result = make_error_record("ERR", "msg")
        assert result["disclaimer"] == DISCLAIMER

    def test_needs_review_all(self):
        result = make_error_record("ERR", "msg")
        assert "all" in result["needs_review"]

    def test_empty_lists(self):
        result = make_error_record("ERR", "msg")
        assert result["medicines"] == []
        assert result["tests"] == []
