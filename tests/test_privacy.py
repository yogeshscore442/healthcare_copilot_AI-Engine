"""
test_privacy.py — Unit tests for privacy.py PII masking.
Run: pytest tests/test_privacy.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.privacy import mask_text


class TestPhoneMasking:
    def test_10_digit_phone(self):
        assert "[PHONE]" in mask_text("Call 9876543210 for details")

    def test_with_plus91(self):
        assert "[PHONE]" in mask_text("Mobile: +91 9876543210")

    def test_with_zero_prefix(self):
        result = mask_text("Ph: 09876543210")
        # May or may not match depending on regex; check no raw 10-digit leaks
        assert "9876543210" not in result or "[PHONE]" in result


class TestEmailMasking:
    def test_basic_email(self):
        assert "[EMAIL]" in mask_text("Contact patient@email.com for records")

    def test_complex_email(self):
        assert "[EMAIL]" in mask_text("Send to john.doe+1@hospital.co.in")


class TestAadhaarMasking:
    def test_aadhaar_spaced(self):
        assert "[AADHAAR]" in mask_text("Aadhaar: 1234 5678 9012")

    def test_aadhaar_in_sentence(self):
        result = mask_text("Patient ID 1234 5678 9012 verified")
        assert "1234 5678 9012" not in result


class TestIdNumberMasking:
    def test_mrn(self):
        assert "[ID_NUM]" in mask_text("MRN: 100234")

    def test_uhid(self):
        assert "[ID_NUM]" in mask_text("UHID 45678")

    def test_pid(self):
        assert "[ID_NUM]" in mask_text("PID: 999001")


class TestPatientNameMasking:
    def test_patient_label(self):
        result = mask_text("Patient: Ravi Kumar, Age 45")
        assert "Ravi Kumar" not in result

    def test_patient_name_label(self):
        result = mask_text("Patient Name: Priya Shankar")
        assert "Priya Shankar" not in result


class TestNonMasking:
    """Clinical values must NOT be masked."""

    def test_test_value_not_masked(self):
        text = "HbA1c: 7.8 %, Reference: 4.0 - 5.6"
        result = mask_text(text)
        assert "7.8" in result
        assert "HbA1c" in result

    def test_medicine_not_masked(self):
        text = "Metformin 500 mg 1-0-1"
        result = mask_text(text)
        assert "Metformin" in result
        assert "500 mg" in result

    def test_date_not_masked(self):
        text = "Report date: 2024-09-15"
        result = mask_text(text)
        assert "2024-09-15" in result

    def test_doctor_name_not_masked(self):
        # Doctor names are not PII in this context
        text = "Dr. S. Krishnamurthy, MBBS, MD"
        result = mask_text(text)
        assert "Krishnamurthy" in result


class TestIdempotency:
    def test_double_masking_safe(self):
        text = "Patient: John Doe, 9876543210"
        once = mask_text(text)
        twice = mask_text(once)
        assert once == twice
