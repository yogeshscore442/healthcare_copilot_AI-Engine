"""
Unit tests for PMBJP Jan Aushadhi generic affordability engine.
Tests deterministic cost calculations, generic matching, and fallback guarantees.
"""
from ai_engine.affordability import calculate_prescription_savings


def test_savings_calculation_known_brands():
    meds = [
        {"name_raw": "Augmentin 625", "generic": "Amoxicillin and Clavulanate"},
        {"name_raw": "Pan 40", "generic": "Pantoprazole"},
        {"name_raw": "Glycomet 500", "generic": "Metformin"},
    ]
    result = calculate_prescription_savings(meds)
    assert result["matched_count"] == 3
    assert result["total_market_cost_inr"] > result["total_jan_aushadhi_cost_inr"]
    assert result["total_savings_inr"] > 200.0
    assert result["savings_percentage"] > 50.0  # Jan Aushadhi typically saves > 50%
    assert len(result["alternatives"]) == 3
    assert "doctor or licensed pharmacist" in result["advisory"]


def test_savings_empty_medications():
    result = calculate_prescription_savings([])
    assert result["matched_count"] == 0
    assert result["total_savings_inr"] == 0.0
    assert result["alternatives"] == []


def test_savings_unknown_medications():
    meds = [{"name_raw": "NonexistentExperimentalDrug 999"}]
    result = calculate_prescription_savings(meds)
    assert result["matched_count"] == 0
    assert result["total_savings_inr"] == 0.0


def test_safety_advisory_wording():
    meds = [{"name_raw": "Telma 40"}]
    result = calculate_prescription_savings(meds)
    # Must NOT advise stopping or switching directly
    assert "you should stop" not in result["advisory"].lower()
    assert "you must switch" not in result["advisory"].lower()
    assert "consult" in result["advisory"].lower()
