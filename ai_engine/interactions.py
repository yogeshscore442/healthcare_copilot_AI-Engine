"""
Clinical Drug-Drug Interaction (DDI) & Patient Advisory Engine.
Deterministically cross-references extracted medications against validated clinical rules.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

_ROOT = os.path.dirname(os.path.abspath(__file__))
_DDI_FILE = os.path.join(_ROOT, "ddi_rules.json")

_RULES_CACHE: Optional[Dict[str, Any]] = None


def _load_rules() -> Dict[str, Any]:
    global _RULES_CACHE
    if _RULES_CACHE is None:
        try:
            with open(_DDI_FILE, "r", encoding="utf-8") as f:
                _RULES_CACHE = json.load(f)
        except Exception:
            _RULES_CACHE = {"interactions": [], "advisories": {}}
    return _RULES_CACHE


def _normalize_drug_name(name: str) -> str:
    """Normalize drug name for matching: lowercase, strip punctuation, remove salts."""
    if not name:
        return ""
    clean = name.lower().strip()
    # Strip strength / numbers e.g. "500 mg", "10mg"
    clean = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|iu| tablet| tab| cap| syrup)?\b", "", clean)
    clean = re.sub(r"[^\w\s]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    # Map common salt stems
    clean = clean.replace("sodium", "").replace("potassium", "").replace("hydrochloride", "").replace("hcl", "")
    return clean.strip()


def check_drug_interactions(medicines: List[Any]) -> List[Dict[str, Any]]:
    """
    Check for clinical drug-drug interactions among extracted medicines.
    
    Parameters
    ----------
    medicines : list
        List of MedicineRecord instances or medicine dictionaries.
        
    Returns
    -------
    list of dict
        Detected clinical interaction alerts with severity, mechanism, and bilingual advice.
    """
    rules = _load_rules()
    interactions = rules.get("interactions", [])
    if not medicines or len(medicines) < 2 or not interactions:
        return []

    # Extract all generic and raw tokens for each medicine
    med_tokens = []
    for m in medicines:
        if hasattr(m, "generic"):
            gen = m.generic or ""
            raw = getattr(m, "name_raw", "")
        elif isinstance(m, dict):
            gen = m.get("generic") or ""
            raw = m.get("name_raw") or m.get("name") or ""
        else:
            gen, raw = "", str(m)

        normalized = set()
        for s in (gen, raw):
            n = _normalize_drug_name(s)
            if n:
                normalized.add(n)
                # Add individual words longer than 3 chars
                for word in n.split():
                    if len(word) > 3:
                        normalized.add(word)
        med_tokens.append({"raw": raw, "generic": gen, "tokens": normalized})

    alerts: List[Dict[str, Any]] = []
    seen_pairs = set()

    for i in range(len(med_tokens)):
        for j in range(i + 1, len(med_tokens)):
            tokens_a = med_tokens[i]["tokens"]
            tokens_b = med_tokens[j]["tokens"]

            for rule in interactions:
                ra = rule["drug_a"].lower()
                rb = rule["drug_b"].lower()

                match_direct = any(ra in t for t in tokens_a) and any(rb in t for t in tokens_b)
                match_reverse = any(rb in t for t in tokens_a) and any(ra in t for t in tokens_b)

                if match_direct or match_reverse:
                    pair_key = tuple(sorted([rule["drug_a"], rule["drug_b"]]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    alerts.append({
                        "drug_a": med_tokens[i]["generic"] or med_tokens[i]["raw"],
                        "drug_b": med_tokens[j]["generic"] or med_tokens[j]["raw"],
                        "rule_pair": f"{rule['drug_a'].capitalize()} + {rule['drug_b'].capitalize()}",
                        "severity": rule.get("severity", "WARNING"),
                        "category": rule.get("category", "General Drug Interaction"),
                        "mechanism": rule.get("mechanism", ""),
                        "clinical_advice": rule.get("clinical_advice", ""),
                        "advice_ta": rule.get("advice_ta", ""),
                    })

    # Sort alerts by severity: SEVERE first, then HIGH, then MODERATE
    severity_order = {"SEVERE": 0, "HIGH": 1, "MODERATE": 2, "WARNING": 3}
    alerts.sort(key=lambda a: severity_order.get(a.get("severity", "WARNING"), 99))
    return alerts


def get_drug_advisories(medicines: List[Any]) -> List[Dict[str, Any]]:
    """
    Get clinical food timing and lifestyle advisories for extracted medicines.
    
    Returns
    -------
    list of dict
        Specific patient administration instructions in English and Tamil.
    """
    rules = _load_rules()
    advisories_db = rules.get("advisories", {})
    if not medicines or not advisories_db:
        return []

    results = []
    seen = set()

    for m in medicines:
        if hasattr(m, "generic"):
            gen = m.generic or ""
            raw = getattr(m, "name_raw", "")
        elif isinstance(m, dict):
            gen = m.get("generic") or ""
            raw = m.get("name_raw") or m.get("name") or ""
        else:
            gen, raw = "", str(m)

        lookup_keys = []
        for s in (gen, raw):
            n = _normalize_drug_name(s)
            if n:
                lookup_keys.append(n)
                lookup_keys.extend(n.split())

        for key, adv in advisories_db.items():
            if key in seen:
                continue
            if any(key in lk for lk in lookup_keys):
                seen.add(key)
                results.append({
                    "medicine": gen or raw,
                    "food_timing": adv.get("food_timing"),
                    "schedule_advice": adv.get("schedule_advice"),
                    "schedule_advice_ta": adv.get("schedule_advice_ta"),
                })

    return results
