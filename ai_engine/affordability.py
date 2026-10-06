"""
Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP) Generic Affordability Engine.
Deterministically computes cost-savings between branded medications and Jan Aushadhi generic equivalents.
"""
from __future__ import annotations

import csv
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.abspath(__file__))
_CSV_FILE = os.path.join(_ROOT, "jan_aushadhi.csv")

_CACHE_MAP: Optional[Dict[str, Dict[str, Any]]] = None


def _clean_token(text: str) -> str:
    if not text:
        return ""
    clean = text.lower().strip()
    clean = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|iu| tablet| tab| cap| syrup)?\b", "", clean)
    clean = re.sub(r"[^\w\s]", " ", clean)
    return re.sub(r"\s+", " ", clean).strip()


def _load_jan_aushadhi_db() -> Dict[str, Dict[str, Any]]:
    global _CACHE_MAP
    if _CACHE_MAP is not None:
        return _CACHE_MAP

    db: Dict[str, Dict[str, Any]] = {}
    if not os.path.exists(_CSV_FILE):
        _CACHE_MAP = db
        return _CACHE_MAP

    try:
        with open(_CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row.get("brand", "").strip()
                if not brand:
                    continue
                try:
                    m_price = float(row.get("market_price_inr", 0.0))
                    j_price = float(row.get("jan_aushadhi_price_inr", 0.0))
                except (ValueError, TypeError):
                    continue

                entry = {
                    "brand": brand,
                    "generic": row.get("generic", "").strip(),
                    "strength": row.get("strength", "").strip(),
                    "market_price_inr": m_price,
                    "jan_aushadhi_price_inr": j_price,
                    "unit": row.get("unit", "").strip(),
                    "source": row.get("source", "PMBJP 2024"),
                    "savings_inr": max(0.0, round(m_price - j_price, 2)),
                }
                # Index by exact lower brand, cleaned token, and generic lower
                db[brand.lower()] = entry
                clean_b = _clean_token(brand)
                if clean_b and clean_b not in db:
                    db[clean_b] = entry

        _CACHE_MAP = db
    except Exception as e:
        logger.warning("Failed to load Jan Aushadhi DB: %s", e)
        _CACHE_MAP = {}

    return _CACHE_MAP


def calculate_prescription_savings(medicines: List[Any]) -> Dict[str, Any]:
    """
    Calculate prescription generic alternatives and potential cost savings via PMBJP Jan Aushadhi.
    
    Parameters
    ----------
    medicines : list
        Extracted list of MedicineRecord objects or medicine dictionaries.
        
    Returns
    -------
    dict
        Structured summary with total market cost, generic cost, savings, and individual alternatives.
        Never raises — returns empty fallback dictionary on error.
    """
    fallback_result = {
        "matched_count": 0,
        "total_market_cost_inr": 0.0,
        "total_jan_aushadhi_cost_inr": 0.0,
        "total_savings_inr": 0.0,
        "savings_percentage": 0.0,
        "alternatives": [],
        "advisory": (
            "Consult your prescribing doctor or licensed pharmacist before substituting "
            "any brand-name medication with a Jan Aushadhi generic equivalent."
        ),
        "advisory_ta": (
            "பிராண்டட் மருந்துகளுக்குப் பதிலாக ஜன் ஔஷதி ஜெனரிக் மருந்துகளைப் பயன்படுத்துவதற்கு "
            "முன் உங்கள் மருத்துவர் அல்லது மருந்தாளுநரிடம் ஆலோசிக்கவும்."
        ),
    }

    try:
        if not medicines:
            return fallback_result

        db = _load_jan_aushadhi_db()
        if not db:
            return fallback_result

        matched_alternatives: List[Dict[str, Any]] = []
        seen_brands = set()

        for m in medicines:
            if hasattr(m, "name_raw"):
                raw_name = m.name_raw or ""
                gen_name = getattr(m, "generic", "") or ""
            elif isinstance(m, dict):
                raw_name = m.get("name_raw") or m.get("name") or ""
                gen_name = m.get("generic") or ""
            else:
                raw_name = str(m)
                gen_name = ""

            # Try matching strategies
            match: Optional[Dict[str, Any]] = None

            # 1. Exact / substring in raw_name
            raw_lower = raw_name.lower().strip()
            if raw_lower in db:
                match = db[raw_lower]
            else:
                # 2. Tokenized match
                token = _clean_token(raw_name)
                if token in db:
                    match = db[token]
                else:
                    # 3. Substring match across db keys
                    for k, v in db.items():
                        if k in raw_lower or raw_lower.startswith(k):
                            match = v
                            break

            # 4. Fallback match by generic name
            if not match and gen_name:
                gen_clean = _clean_token(gen_name)
                for v in db.values():
                    if _clean_token(v["generic"]) == gen_clean:
                        match = v
                        break

            if match:
                b_name = match["brand"]
                if b_name in seen_brands:
                    continue
                seen_brands.add(b_name)

                matched_alternatives.append({
                    "prescribed_name": raw_name,
                    "brand": match["brand"],
                    "generic_equivalent": match["generic"],
                    "strength": match["strength"],
                    "market_price_inr": match["market_price_inr"],
                    "jan_aushadhi_price_inr": match["jan_aushadhi_price_inr"],
                    "unit": match["unit"],
                    "savings_inr": match["savings_inr"],
                    "savings_percentage": round(
                        (match["savings_inr"] / match["market_price_inr"] * 100)
                        if match["market_price_inr"] > 0
                        else 0.0,
                        1,
                    ),
                    "source": match.get("source", "PMBJP 2024"),
                })

        if not matched_alternatives:
            return fallback_result

        tot_market = round(sum(a["market_price_inr"] for a in matched_alternatives), 2)
        tot_ja = round(sum(a["jan_aushadhi_price_inr"] for a in matched_alternatives), 2)
        tot_savings = round(tot_market - tot_ja, 2)
        pct_savings = round((tot_savings / tot_market * 100) if tot_market > 0 else 0.0, 1)

        return {
            "matched_count": len(matched_alternatives),
            "total_market_cost_inr": tot_market,
            "total_jan_aushadhi_cost_inr": tot_ja,
            "total_savings_inr": tot_savings,
            "savings_percentage": pct_savings,
            "alternatives": matched_alternatives,
            "advisory": fallback_result["advisory"],
            "advisory_ta": fallback_result["advisory_ta"],
        }

    except Exception as e:
        logger.warning("Error in calculate_prescription_savings: %s", e)
        return fallback_result
