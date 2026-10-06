"""
Unit tests for ABDM / FHIR R4 Bundle converter.
"""
from ai_engine.fhir import record_to_fhir_bundle


def test_fhir_bundle_structure():
    mock_record = {
        "record_id": "test-rec-123",
        "doc_type": "lab_report",
        "doc_date": "2024-10-01",
        "tests": [
            {
                "name": "Hemoglobin",
                "loinc": "718-7",
                "value": 14.2,
                "unit": "g/dL",
                "ref_low": 13.0,
                "ref_high": 17.0,
                "flag": "NORMAL",
            }
        ],
        "medicines": [],
        "diagnoses": [],
    }
    bundle = record_to_fhir_bundle(mock_record)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert len(bundle["entry"]) >= 3  # Composition, Patient, Observation, DiagnosticReport
    types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Composition" in types
    assert "Patient" in types
    assert "Observation" in types
    assert "DiagnosticReport" in types


def test_fhir_medication_request():
    mock_record = {
        "record_id": "test-med-456",
        "doc_type": "prescription",
        "doc_date": "2024-10-01",
        "tests": [],
        "medicines": [
            {
                "name_raw": "Augmentin 625",
                "generic": "Amoxicillin and Clavulanate",
                "strength": "625 mg",
                "schedule_parsed": ["morning", "night"],
                "food_instruction": "after_food",
                "duration_days": 5,
            }
        ],
        "diagnoses": [{"text": "Bacterial Sinusitis", "icd10": "J01.90"}],
    }
    bundle = record_to_fhir_bundle(mock_record)
    types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "MedicationRequest" in types
    assert "Condition" in types
