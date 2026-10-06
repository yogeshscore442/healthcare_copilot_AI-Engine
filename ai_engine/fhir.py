"""
HL7 FHIR Release 4 & ABDM (Ayushman Bharat Digital Mission) Converter.
Converts AI Health Copilot extracted health records into ABDM-compliant FHIR R4 Bundles.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _interpretation_code(flag: str) -> Dict[str, Any]:
    flag_u = (flag or "").upper()
    code_map = {
        "HIGH": {"code": "H", "display": "High"},
        "LOW": {"code": "L", "display": "Low"},
        "NORMAL": {"code": "N", "display": "Normal"},
    }
    interp = code_map.get(flag_u, {"code": "IND", "display": "Indeterminate"})
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": interp["code"],
                "display": interp["display"],
            }
        ],
        "text": interp["display"],
    }


def record_to_fhir_bundle(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an AI Health Copilot health record dictionary into an ABDM FHIR R4 Bundle.
    
    Parameters
    ----------
    record : dict
        Standard extracted HealthRecord dictionary.
        
    Returns
    -------
    dict
        HL7 FHIR R4 Document Bundle adhering to ABDM specifications.
    """
    record_id = record.get("record_id") or str(uuid.uuid4())
    doc_type = record.get("doc_type", "diagnostic_report")
    doc_date = record.get("doc_date") or _now_iso()[:10]
    bundle_id = f"bundle-{record_id}"

    patient_ref = f"urn:uuid:{uuid.uuid4()}"
    composition_ref = f"urn:uuid:{uuid.uuid4()}"

    entries: List[Dict[str, Any]] = []

    # 1. Composition Resource (Document Header for ABDM)
    doc_type_display = {
        "lab_report": "Diagnostic Report / Laboratory Record",
        "prescription": "Prescription Record",
        "discharge_summary": "Discharge Summary Document",
        "diagnostic_report": "Diagnostic Report",
    }.get(doc_type, "Health Record Document")

    composition: Dict[str, Any] = {
        "fullUrl": composition_ref,
        "resource": {
            "resourceType": "Composition",
            "id": f"comp-{record_id}",
            "identifier": {
                "system": "https://abdm.gov.in/fhir/composition",
                "value": f"ABDM-COMP-{record_id[:8]}",
            },
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "419891008",
                        "display": doc_type_display,
                    }
                ],
                "text": doc_type_display,
            },
            "subject": {"reference": patient_ref, "display": "Patient"},
            "date": f"{doc_date}T00:00:00Z" if len(doc_date) == 10 else _now_iso(),
            "title": f"ABDM {doc_type_display}",
            "section": [],
        },
    }

    # 2. Patient Resource
    patient: Dict[str, Any] = {
        "fullUrl": patient_ref,
        "resource": {
            "resourceType": "Patient",
            "id": f"pat-{record_id}",
            "identifier": [
                {
                    "system": "https://healthid.ndhm.gov.in",
                    "type": {
                        "coding": [
                            {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}
                        ]
                    },
                    "value": f"ABHA-{record_id[:8].upper()}",
                }
            ],
            "active": True,
            "name": [
                {
                    "text": "De-Identified Patient" if not record.get("patient_name_present") else "Patient Record"
                }
            ],
        },
    }
    entries.append(patient)

    # 3. Observations & DiagnosticReport (for lab tests)
    tests = record.get("tests", [])
    observation_refs = []

    for idx, test in enumerate(tests):
        obs_id = str(uuid.uuid4())
        obs_ref = f"urn:uuid:{obs_id}"
        observation_refs.append(obs_ref)

        loinc = test.get("loinc") or "30745-4"
        test_name = test.get("name", "Laboratory Test")
        flag = test.get("flag", "UNKNOWN")

        obs_resource: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": f"obs-{idx+1}-{record_id[:8]}",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc,
                        "display": test_name,
                    }
                ],
                "text": test_name,
            },
            "subject": {"reference": patient_ref},
            "effectiveDateTime": f"{doc_date}T00:00:00Z" if len(doc_date) == 10 else _now_iso(),
            "interpretation": [_interpretation_code(flag)],
        }

        if test.get("value") is not None:
            unit = test.get("unit") or ""
            obs_resource["valueQuantity"] = {
                "value": test["value"],
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit,
            }
        elif test.get("value_text"):
            obs_resource["valueString"] = test["value_text"]

        if test.get("ref_low") is not None or test.get("ref_high") is not None:
            ref_range: Dict[str, Any] = {}
            if test.get("ref_low") is not None:
                ref_range["low"] = {"value": test["ref_low"], "unit": test.get("unit", "")}
            if test.get("ref_high") is not None:
                ref_range["high"] = {"value": test["ref_high"], "unit": test.get("unit", "")}
            obs_resource["referenceRange"] = [ref_range]

        entries.append({"fullUrl": obs_ref, "resource": obs_resource})

    if observation_refs or tests:
        diag_id = str(uuid.uuid4())
        diag_ref = f"urn:uuid:{diag_id}"
        diag_report = {
            "fullUrl": diag_ref,
            "resource": {
                "resourceType": "DiagnosticReport",
                "id": f"diag-{record_id[:8]}",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "LAB", "display": "Laboratory"}
                        ]
                    }
                ],
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "11502-2", "display": "Laboratory report"}],
                    "text": "Clinical Laboratory Diagnostic Report",
                },
                "subject": {"reference": patient_ref},
                "effectiveDateTime": f"{doc_date}T00:00:00Z" if len(doc_date) == 10 else _now_iso(),
                "result": [{"reference": o_ref} for o_ref in observation_refs],
            },
        }
        entries.append(diag_report)
        composition["resource"]["section"].append({
            "title": "Laboratory & Diagnostic Observations",
            "entry": [{"reference": diag_ref}] + [{"reference": o} for o in observation_refs],
        })

    # 4. MedicationRequest resources (for medicines)
    medicines = record.get("medicines", [])
    med_refs = []

    for idx, med in enumerate(medicines):
        med_id = str(uuid.uuid4())
        med_ref = f"urn:uuid:{med_id}"
        med_refs.append(med_ref)

        name_raw = med.get("name_raw", "Medication")
        generic = med.get("generic") or name_raw
        strength = med.get("strength") or ""
        food_instr = med.get("food_instruction") or ""
        schedule = med.get("schedule_parsed") or []

        freq_text = " / ".join(schedule) if schedule else (med.get("schedule_raw") or "Once daily")
        food_text = "Before Food" if food_instr == "before_food" else ("After Food" if food_instr == "after_food" else "")

        med_resource: Dict[str, Any] = {
            "resourceType": "MedicationRequest",
            "id": f"med-{idx+1}-{record_id[:8]}",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "https://abdm.gov.in/nlem",
                        "display": f"{generic} {strength}".strip(),
                    }
                ],
                "text": f"{name_raw} ({generic})".strip(),
            },
            "subject": {"reference": patient_ref},
            "authoredOn": f"{doc_date}T00:00:00Z" if len(doc_date) == 10 else _now_iso(),
            "dosageInstruction": [
                {
                    "text": f"{freq_text} {food_text}".strip(),
                    "timing": {
                        "code": {"text": freq_text}
                    },
                    "additionalInstruction": [{"text": food_text}] if food_text else [],
                }
            ],
        }

        if med.get("duration_days"):
            med_resource["dispenseRequest"] = {
                "expectedSupplyDuration": {
                    "value": med["duration_days"],
                    "unit": "days",
                    "system": "http://unitsofmeasure.org",
                    "code": "d",
                }
            }

        entries.append({"fullUrl": med_ref, "resource": med_resource})

    if med_refs:
        composition["resource"]["section"].append({
            "title": "Prescribed Medications",
            "entry": [{"reference": m} for m in med_refs],
        })

    # 5. Condition resources (for diagnoses / ICD-10)
    diagnoses = record.get("diagnoses", [])
    cond_refs = []

    for idx, diag in enumerate(diagnoses):
        cond_id = str(uuid.uuid4())
        cond_ref = f"urn:uuid:{cond_id}"
        cond_refs.append(cond_ref)

        diag_text = diag.get("text", "Clinical Condition")
        icd10 = diag.get("icd10")

        codings = []
        if icd10:
            codings.append({
                "system": "http://hl7.org/fhir/sid/icd-10",
                "code": icd10,
                "display": diag_text,
            })

        cond_resource: Dict[str, Any] = {
            "resourceType": "Condition",
            "id": f"cond-{idx+1}-{record_id[:8]}",
            "clinicalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
            },
            "code": {
                "coding": codings,
                "text": diag_text,
            },
            "subject": {"reference": patient_ref},
            "recordedDate": doc_date,
        }
        entries.append({"fullUrl": cond_ref, "resource": cond_resource})

    if cond_refs:
        composition["resource"]["section"].append({
            "title": "Diagnosed Conditions",
            "entry": [{"reference": c} for c in cond_refs],
        })

    # Put Composition at the very beginning of entries (standard FHIR document convention)
    all_entries = [composition] + entries

    # Assemble FHIR Bundle
    bundle: Dict[str, Any] = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": _now_iso(),
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"],
        },
        "identifier": {
            "system": "https://abdm.gov.in/bundle",
            "value": f"ABDM-DOC-{record_id[:8].upper()}",
        },
        "type": "document",
        "timestamp": _now_iso(),
        "total": len(all_entries),
        "entry": all_entries,
    }

    return bundle


def export_fhir_json(record: Dict[str, Any], filepath: str) -> None:
    """Save an ABDM FHIR R4 Bundle to file."""
    bundle = record_to_fhir_bundle(record)
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)
