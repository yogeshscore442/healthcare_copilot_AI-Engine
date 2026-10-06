"""
Unit tests for Drug-Drug Interaction (DDI) & Clinical Advisories.
"""
from ai_engine.interactions import check_drug_interactions, get_drug_advisories


def test_ddi_aspirin_clopidogrel():
    meds = [
        {"name_raw": "Ecosprin 75", "generic": "Aspirin"},
        {"name_raw": "Clopilet 75", "generic": "Clopidogrel"},
    ]
    alerts = check_drug_interactions(meds)
    assert len(alerts) >= 1
    pair = alerts[0]
    assert pair["severity"] in ("HIGH", "SEVERE", "MODERATE")
    assert "bleeding" in pair["mechanism"].lower()
    assert pair["advice_ta"] != ""


def test_ddi_sildenafil_nitroglycerin():
    meds = [
        {"name_raw": "Suhagra 50", "generic": "Sildenafil"},
        {"name_raw": "Nitrocontin 2.6", "generic": "Nitroglycerin"},
    ]
    alerts = check_drug_interactions(meds)
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == "SEVERE"


def test_ddi_no_interaction():
    meds = [
        {"name_raw": "Paracetamol 500", "generic": "Paracetamol"},
        {"name_raw": "Amoxicillin 500", "generic": "Amoxicillin"},
    ]
    alerts = check_drug_interactions(meds)
    assert len(alerts) == 0


def test_drug_advisories():
    meds = [
        {"name_raw": "Thyronorm 50", "generic": "Levothyroxine"},
        {"name_raw": "Glycomet 500", "generic": "Metformin"},
    ]
    advs = get_drug_advisories(meds)
    assert len(advs) >= 1
    timings = [a["food_timing"] for a in advs]
    assert "empty_stomach" in timings or "after_food" in timings
