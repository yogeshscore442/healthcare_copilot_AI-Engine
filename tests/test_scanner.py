import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_engine.summarize import _safety_check, _grounding_check


def _rec(tests=None, meds=None):
    return {"tests": tests or [], "medicines": meds or [], "diagnoses": []}


class TestForbiddenPhrases:
    def test_diagnosed_with(self): assert not _safety_check("The patient is diagnosed with diabetes.")
    def test_you_have(self): assert not _safety_check("It looks like you have hypertension.")
    def test_you_are_diagnosed(self): assert not _safety_check("You are diagnosed with anaemia.")
    def test_your_diagnosis(self): assert not _safety_check("Your diagnosis is type 2 diabetes.")
    def test_you_should_take(self): assert not _safety_check("You should take Metformin twice a day.")
    def test_increase_dose(self): assert not _safety_check("Please increase your dose of insulin.")
    def test_decrease_dose(self): assert not _safety_check("Decrease your dose if sugar drops.")
    def test_stop_taking(self): assert not _safety_check("Stop taking Aspirin immediately.")
    def test_drug_interaction(self): assert not _safety_check("There is a drug interaction between warfarin and aspirin.")
    def test_contraindicated(self): assert not _safety_check("This drug is contraindicated in renal failure.")
    def test_side_effect(self): assert not _safety_check("Common side effects include nausea.")
    def test_treatment_plan(self): assert not _safety_check("Follow the treatment plan prescribed.")
    def test_medical_advice(self): assert not _safety_check("This constitutes medical advice from the AI.")
    def test_recommend_taking(self): assert not _safety_check("It is recommended taking 500 mg twice daily.")
    def test_prescribe(self): assert not _safety_check("The AI will prescribe additional tests.")
    def test_case_upper(self): assert not _safety_check("DIAGNOSED WITH chronic kidney disease.")
    def test_case_mixed(self): assert not _safety_check("Looks like You Have elevated cholesterol.")


class TestSafePhrases:
    def test_abnormal_lab(self): assert _safety_check("The HbA1c value is above the usual range. Please discuss with your doctor.")
    def test_normal_value(self): assert _safety_check("The Creatinine is within the usual range.")
    def test_medicine_listing(self): assert _safety_check("This record lists medicines: Metformin 500mg.")
    def test_disclaimer(self): assert _safety_check("This is AI-generated information. It is not a diagnosis or medical advice. Please consult your doctor.")
    def test_tamil(self): assert _safety_check("" )


class TestGroundingFails:
    def test_hallucinated_value(self):
        r = _rec(tests=[{"name": "HbA1c", "value": 7.8, "ref_low": 4.0, "ref_high": 5.6}])
        assert not _grounding_check("The HbA1c is 9.5.", r)

    def test_hallucinated_duration(self):
        r = _rec(meds=[{"name_raw": "Metformin", "duration_days": 10, "strength": "500mg"}])
        assert not _grounding_check("30 days of Metformin.", r)

    def test_fabricated_ref_high(self):
        r = _rec(tests=[{"name": "Glucose", "value": 110.0, "ref_low": 70.0, "ref_high": 100.0}])
        assert not _grounding_check("Glucose is above usual range, upper limit 120.", r)


class TestGroundingPasses:
    def test_grounded_value(self):
        r = _rec(tests=[{"name": "HbA1c", "value": 7.8, "ref_low": 4.0, "ref_high": 5.6}])
        assert _grounding_check("HbA1c 7.8 is above 4.0 to 5.6.", r)

    def test_no_numbers_in_summary(self):
        assert _grounding_check("Please review this record with your doctor.", _rec())

    def test_safe_incidental_numbers(self):
        assert _grounding_check("This report shows 2 results reviewed.", _rec())

    def test_duration_grounded(self):
        r = _rec(meds=[{"name_raw": "Amoxicillin", "duration_days": 7, "strength": "250mg"}])
        assert _grounding_check("7 days of Amoxicillin 250mg.", r)
