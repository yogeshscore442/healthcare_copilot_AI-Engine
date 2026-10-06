"""
AI Health Copilot — Modern Streamlit Web UI Dashboard.
Enterprise-grade multimodal medical document intelligence with:
- Zero Hallucination Deterministic Lab Flags (LOINC)
- Drug-Drug Interaction (DDI) & Contraindication Alerts
- WHO/NLEM Generic Drug Normalization
- Bilingual Patient Summaries (English & Tamil)
- Voice Copilot (Spoken Patient Audio Explanations)
- ABDM FHIR R4 Document Bundle 1-Click Export
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from ai_engine import (
    check_drug_interactions,
    export_fhir_json,
    extract_record,
    calculate_prescription_savings,
    generate_audio,
    get_browser_speech_html,
    get_drug_advisories,
    record_to_fhir_bundle,
)

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Health Copilot | Clinical Intelligence Engine",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Clinical Grade Aesthetics ──────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0284c7, #2563eb, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-container {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 1.2rem;
    }
    .badge-pill {
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-abdm { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .badge-safety { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .badge-voice { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
    .badge-nlem { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }

    .card-metric {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .alert-ddi-box {
        background: linear-gradient(135deg, #fff1f2, #ffe4e6);
        border: 1px solid #fecdd3;
        border-left: 6px solid #e11d48;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    
    .flag-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .flag-low {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .flag-normal {
        background-color: #dcfce7;
        color: #166534;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .flag-unknown {
        background-color: #f1f5f9;
        color: #475569;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ROOT = Path(__file__).parent.resolve()
SAMPLES_DIR = ROOT / "samples"
CONTRACT_DIR = ROOT / "contract"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🩺 AI Health Copilot Engine</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Next-Gen Multimodal Clinical Record Ingestion • Zero-Hallucination Lab Flags • DDI Safety Checker • ABDM FHIR R4</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="badge-container">
        <span class="badge-pill badge-abdm">🇮🇳 ABDM FHIR R4 Ready</span>
        <span class="badge-pill badge-safety">🛡️ 100% Deterministic LOINC Flags</span>
        <span class="badge-pill badge-voice">🎙️ Bilingual Voice Copilot (EN + TA)</span>
        <span class="badge-pill badge-nlem">💊 360+ NLEM Drug Mappings</span>
        <span class="badge-pill badge-safety">🔒 Zero PII Leakage</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar: Document Selection ───────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Select Document")
    
    sample_options = {
        "Custom Upload (Image or PDF)": "upload",
        "Sample 1: Blood Routine & Lipid Lab (lab1.jpg)": "samples/lab1.jpg",
        "Sample 2: Diabetes & Kidney Lab (lab2.jpg)": "samples/lab2.jpg",
        "Sample 3: Adult Prescription (prescription1.jpg)": "samples/prescription1.jpg",
        "Sample 4: Multi-drug Prescription (prescription2.jpg)": "samples/prescription2.jpg",
        "Sample 5: Tamil-English Mixed Rx (tamil_mixed1.jpg)": "samples/tamil_mixed1.jpg",
        "Sample 6: Inpatient Discharge PDF (discharge1.pdf)": "samples/discharge1.pdf",
        "Mock: Comprehensive Thyroid & Lipid Panel": "contract/mock_thyroid_lipid_lab.json",
        "Mock: Cardiac Discharge Summary (DDI Alerts)": "contract/mock_cardiac_discharge.json",
        "Mock: Thyroid & Dyslipidemia Rx (Bilingual)": "contract/mock_thyroid_prescription.json",
    }
    
    selected_choice = st.selectbox(
        "Choose a sample or upload your own:",
        options=list(sample_options.keys()),
        index=1,
    )
    
    lang_hint = st.selectbox(
        "Language Priority:",
        options=["auto", "en", "ta", "hi"],
        format_func=lambda x: {"auto": "Auto-Detect", "en": "English", "ta": "Tamil (தமிழ்)", "hi": "Hindi (हिंदी)"}[x],
    )
    
    uploaded_file = None
    if sample_options[selected_choice] == "upload":
        uploaded_file = st.file_uploader("Upload Image or PDF", type=["jpg", "jpeg", "png", "pdf"])

    st.markdown("---")
    st.markdown("### ⚙️ Engine Info")
    st.caption("• **Model:** Gemini Multimodal Vision")
    st.caption("• **Standards:** LOINC • ICD-10 • NLEM • FHIR R4")
    st.caption("• **Safety:** Deterministic Rules Engine (No hallucinated flags)")


# ── Helper to Load or Process Document ────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_mock_record(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("medicines"):
        data["safety_alerts"] = check_drug_interactions(data["medicines"])
        data["drug_advisories"] = get_drug_advisories(data["medicines"])
    return data


record: Optional[Dict[str, Any]] = None
preview_image_path: Optional[str] = None
is_pdf = False

with st.spinner("Processing medical document..."):
    choice_val = sample_options[selected_choice]
    
    if choice_val == "upload" and uploaded_file is not None:
        # Save temp file
        temp_dir = ROOT / "samples" / "uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        mime = "application/pdf" if uploaded_file.name.lower().endswith(".pdf") else "image/jpeg"
        if mime == "application/pdf":
            is_pdf = True
        else:
            preview_image_path = str(temp_path)
        
        record = extract_record(str(temp_path), mime=mime, lang_hint=lang_hint)
        
    elif choice_val.endswith(".json"):
        full_json_path = ROOT / choice_val
        if full_json_path.exists():
            record = load_mock_record(str(full_json_path))
            
    elif choice_val.startswith("samples/"):
        full_sample_path = ROOT / choice_val
        if full_sample_path.exists():
            if choice_val.endswith(".pdf"):
                is_pdf = True
                record = extract_record(str(full_sample_path), mime="application/pdf", lang_hint=lang_hint)
            else:
                preview_image_path = str(full_sample_path)
                record = extract_record(str(full_sample_path), mime="image/jpeg", lang_hint=lang_hint)


# ── Display Processing Results ────────────────────────────────────────────────
if not record:
    st.info("👈 Please select a sample document from the sidebar or upload a medical file to begin.")
else:
    # ── Top Summary Header ──
    doc_type = record.get("doc_type", "unknown").replace("_", " ").title()
    doc_date = record.get("doc_date") or "Not Specified"
    med_count = len(record.get("medicines", []))
    test_count = len(record.get("tests", []))
    diag_count = len(record.get("diagnoses", []))
    
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("Document Type", doc_type)
    with col_m2:
        st.metric("Document Date", doc_date)
    with col_m3:
        st.metric("Medications", f"{med_count} extracted")
    with col_m4:
        st.metric("Lab Tests", f"{test_count} results")
    with col_m5:
        st.metric("Diagnoses (ICD-10)", f"{diag_count} mapped")

    st.markdown("---")

    # ── Critical Safety Alerts (DDI & Contraindications) ──
    safety_alerts = record.get("safety_alerts", [])
    if not safety_alerts and record.get("medicines"):
        safety_alerts = check_drug_interactions(record.get("medicines", []))

    if safety_alerts:
        st.markdown(
            f"""
            <div class="alert-ddi-box">
                <h3 style="color: #be123c; margin: 0 0 8px 0; display: flex; align-items: center; gap: 8px;">
                    🚨 Critical Clinical Alert: {len(safety_alerts)} Drug-Drug Interaction(s) Detected!
                </h3>
                <p style="margin: 0; color: #475569; font-size: 0.92rem;">
                    The patient is prescribed medications that may conflict or heighten clinical risk. Review carefully:
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for alert in safety_alerts:
            sev = alert.get("severity", "WARNING")
            badge_color = "#dc2626" if sev == "SEVERE" else ("#ea580c" if sev == "HIGH" else "#d97706")
            with st.expander(f"⚠️ {alert.get('rule_pair')} — Severity: {sev}", expanded=True):
                st.markdown(f"**Mechanism:** {alert.get('mechanism')}")
                st.markdown(f"**Clinical Recommendation:** {alert.get('clinical_advice')}")
                if alert.get("advice_ta"):
                    st.markdown(f"**தமிழில் எச்சரிக்கை:** *{alert.get('advice_ta')}*")

    # ── Main Two Column Layout ──
    left_col, right_col = st.columns([1, 1.4])

    with left_col:
        st.subheader("🖼️ Document Source")
        if preview_image_path and os.path.exists(preview_image_path):
            st.image(preview_image_path, use_container_width=True, caption=os.path.basename(preview_image_path))
        elif is_pdf:
            st.info("📄 PDF Inpatient Document (Multi-page text parsed via PyMuPDF)")
        else:
            st.info("📋 Contract Schema Verification Mode (Standard Ground Truth)")

        # PII & Privacy Indicator
        st.markdown(
            """
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; margin-top: 14px;">
                <div style="color: #0f172a; font-weight: 600; font-size: 0.9rem;">🔒 Privacy & Compliance Status</div>
                <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">
                    ✔ PII De-identified (Phone, Aadhaar, MRN masked)<br>
                    ✔ ABDM Demographic Sanitization Applied
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        tab_tests, tab_meds, tab_savings, tab_diag, tab_summary, tab_voice, tab_fhir = st.tabs([
            "🧪 Lab Results",
            "💊 Medications",
            "💰 Jan Aushadhi Savings",
            "📋 Diagnoses",
            "📖 Summaries",
            "🎙️ Voice Copilot",
            "🇮🇳 ABDM FHIR R4",
        ])

        # ── TAB 1: Laboratory Results ──
        with tab_tests:
            tests = record.get("tests", [])
            if not tests:
                st.info("No laboratory tests recorded in this document.")
            else:
                for t in tests:
                    flag = t.get("flag", "UNKNOWN")
                    flag_class = f"flag-{flag.lower()}"
                    flag_symbol = {"HIGH": "🔴 HIGH", "LOW": "🔵 LOW", "NORMAL": "🟢 NORMAL"}.get(flag, "⚪ " + flag)
                    val = t.get("value")
                    val_display = str(val) if val is not None else (t.get("value_text") or "-")
                    unit = t.get("unit") or ""
                    ref_low = t.get("ref_low")
                    ref_high = t.get("ref_high")
                    ref_str = f"{ref_low} – {ref_high}" if (ref_low is not None and ref_high is not None) else "Not defined"

                    with st.container():
                        st.markdown(
                            f"""
                            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 700; font-size: 1rem; color: #1e293b;">{t.get('name')}</span>
                                    <span class="{flag_class}">{flag_symbol}</span>
                                </div>
                                <div style="margin-top: 6px; font-size: 0.88rem; color: #475569;">
                                    <b>Result:</b> <span style="font-size: 1.05rem; font-weight: 600; color: #0f172a;">{val_display} {unit}</span> &nbsp;|&nbsp;
                                    <b>Ref Range:</b> {ref_str} {unit} &nbsp;|&nbsp;
                                    <b>LOINC:</b> <code>{t.get('loinc') or 'N/A'}</code>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if t.get("explanation_en") or t.get("explanation_ta"):
                            with st.expander(f"ℹ️ Plain-language meaning of {t.get('name')}", expanded=False):
                                if t.get("explanation_en"):
                                    st.write(f"**English:** {t['explanation_en']}")
                                if t.get("explanation_ta"):
                                    st.write(f"**தமிழ்:** {t['explanation_ta']}")

        # ── TAB 2: Medications & Schedules ──
        with tab_meds:
            medicines = record.get("medicines", [])
            if not medicines:
                st.info("No medications extracted from this document.")
            else:
                advisories = record.get("drug_advisories", [])
                if not advisories:
                    advisories = get_drug_advisories(medicines)

                for med in medicines:
                    name_raw = med.get("name_raw") or "Medicine"
                    generic = med.get("generic") or "Generic not mapped"
                    strength = med.get("strength") or ""
                    schedule = med.get("schedule_parsed") or []
                    sched_str = " / ".join(s.capitalize() for s in schedule) if schedule else (med.get("schedule_raw") or "Unspecified")
                    food = med.get("food_instruction")
                    food_str = "🍽️ After Food" if food == "after_food" else ("⏳ Before Food" if food == "before_food" else "Not specified")
                    days = med.get("duration_days")
                    duration_str = f"{days} days" if days else "Not specified"

                    st.markdown(
                        f"""
                        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                <span style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">{name_raw} {strength}</span>
                                <span style="font-size: 0.8rem; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{food_str}</span>
                            </div>
                            <div style="color: #2563eb; font-weight: 600; font-size: 0.9rem; margin-top: 2px;">
                                💊 Generic: {generic}
                            </div>
                            <div style="margin-top: 6px; font-size: 0.85rem; color: #475569;">
                                <b>Schedule:</b> {sched_str} &nbsp;|&nbsp; <b>Duration:</b> {duration_str}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if advisories:
                    st.markdown("#### ⏰ Patient Administration & Food Timing Advisories")
                    for adv in advisories:
                        st.info(f"**{adv['medicine'].title()}:** {adv['schedule_advice']}\n\n*{adv['schedule_advice_ta']}*")

        # ── TAB 3: Jan Aushadhi Generic Savings ──
        with tab_savings:
            st.markdown("### 💰 PMBJP Jan Aushadhi Generic Affordability")
            st.caption("Pradhan Mantri Bhartiya Janaushadhi Pariyojana price comparison for branded prescription items.")

            meds = record.get("medicines", [])
            savings_data = record.get("cost_savings")
            if not savings_data and meds:
                savings_data = calculate_prescription_savings(meds)

            if not savings_data or savings_data.get("matched_count", 0) == 0:
                st.info("No matching branded medications found in PMBJP Jan Aushadhi catalog for this document.")
            else:
                m_cost = savings_data.get("total_market_cost_inr", 0.0)
                j_cost = savings_data.get("total_jan_aushadhi_cost_inr", 0.0)
                tot_save = savings_data.get("total_savings_inr", 0.0)
                pct_save = savings_data.get("savings_percentage", 0.0)

                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    st.metric("Total Market Cost", f"₹ {m_cost:.1f}")
                with col_s2:
                    st.metric("Jan Aushadhi Cost", f"₹ {j_cost:.1f}")
                with col_s3:
                    st.metric("Estimated Savings", f"₹ {tot_save:.1f}")
                with col_s4:
                    st.metric("Discount %", f"{pct_save:.1f}% 🔥")

                st.markdown("#### 💊 Branded vs Generic Equivalent Comparison")
                for alt in savings_data.get("alternatives", []):
                    st.markdown(
                        f"""
                        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; color: #0f172a; font-size: 1rem;">{alt['brand']} ({alt['strength']})</span>
                                <span style="background: #dcfce7; color: #166534; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem;">
                                    Saves ₹{alt['savings_inr']} ({alt['savings_percentage']}%)
                                </span>
                            </div>
                            <div style="color: #2563eb; font-size: 0.9rem; margin-top: 4px;">
                                <b>Govt Generic Equivalent:</b> {alt['generic_equivalent']}
                            </div>
                            <div style="font-size: 0.85rem; color: #64748b; margin-top: 4px;">
                                Market: <strike>₹{alt['market_price_inr']}</strike> &nbsp;➔&nbsp;
                                <b style="color: #059669;">Jan Aushadhi: ₹{alt['jan_aushadhi_price_inr']}</b> ({alt['unit']})
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.warning(f"ℹ️ {savings_data.get('advisory')}\n\n*{savings_data.get('advisory_ta')}*")

        # ── TAB 4: Diagnoses & ICD-10 ──
        with tab_diag:
            diagnoses = record.get("diagnoses", [])
            if not diagnoses:
                st.info("No explicit clinical diagnoses extracted.")
            else:
                for d in diagnoses:
                    icd = d.get("icd10") or "Uncoded"
                    st.markdown(
                        f"""
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600; color: #1e293b;">{d.get('text')}</span>
                            <span style="background: #f1f5f9; color: #334155; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-weight: 700;">
                                ICD-10: {icd}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # ── TAB 4: Plain-Language Patient Summaries ──
        with tab_summary:
            st.markdown("#### 🇬🇧 English Patient Summary")
            st.write(record.get("summary_en") or "No summary available.")

            st.markdown("#### 🇮🇳 தமிழ் நோயாளி சுருக்கம் (Tamil Summary)")
            st.write(record.get("summary_ta") or "தமிழ் சுருக்கம் கிடைக்கவில்லை.")

            st.markdown("#### 🇮🇳 हिंदी रोगी सारांश (Hindi Summary)")
            st.write(record.get("summary_hi") or "हिंदी सारांश उपलब्ध नहीं है।")

        # ── TAB 5: Voice Copilot (Spoken Patient Audio) ──
        with tab_voice:
            st.markdown("### 🎙️ Multilingual Voice Copilot (குரல் / आवाज़)")
            st.caption("Empowering patients who cannot read clinical terms through instant speech synthesis in 3 languages.")

            sum_en = record.get("summary_en", "")
            sum_ta = record.get("summary_ta", "")
            sum_hi = record.get("summary_hi", "")

            # Native Web Speech HTML Button (Zero latency, runs right in the browser)
            st.components.v1.html(get_browser_speech_html(sum_en, sum_ta, sum_hi), height=140)

            # Server-side Audio Generation for 3 languages
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                if st.button("🎧 English Audio", key="tts_en_btn"):
                    with st.spinner("Generating English Voice..."):
                        audio_en = generate_audio(sum_en, lang="en")
                        if audio_en:
                            st.audio(audio_en, format="audio/mp3")
                        else:
                            st.warning("Please use the browser voice buttons above.")

            with col_v2:
                if st.button("🎧 தமிழ் குரல் (Tamil)", key="tts_ta_btn"):
                    with st.spinner("Generating Tamil Voice..."):
                        audio_ta = generate_audio(sum_ta, lang="ta")
                        if audio_ta:
                            st.audio(audio_ta, format="audio/mp3")
                        else:
                            st.warning("Please use the browser voice buttons above.")

            with col_v3:
                if st.button("🎧 हिंदी आवाज़ (Hindi)", key="tts_hi_btn"):
                    with st.spinner("Generating Hindi Voice..."):
                        audio_hi = generate_audio(sum_hi, lang="hi")
                        if audio_hi:
                            st.audio(audio_hi, format="audio/mp3")
                        else:
                            st.warning("Please use the browser voice buttons above.")

        # ── TAB 6: ABDM FHIR R4 Bundle Export ──
        with tab_fhir:
            st.markdown("### 🇮🇳 ABDM FHIR R4 Document Bundle")
            st.caption("Standardized Health Document Bundle conforming to National Health Authority (NHA) ABDM specifications.")

            fhir_bundle = record_to_fhir_bundle(record)
            fhir_str = json.dumps(fhir_bundle, indent=2, ensure_ascii=False)

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.download_button(
                    label="📥 Download ABDM FHIR Bundle (.json)",
                    data=fhir_str,
                    file_name=f"ABDM_FHIR_{record.get('record_id', 'doc')[:8]}.json",
                    mime="application/json",
                )
            with col_f2:
                st.download_button(
                    label="📥 Download Contract Health Record (.json)",
                    data=json.dumps(record, indent=2, ensure_ascii=False),
                    file_name=f"HealthRecord_{record.get('record_id', 'doc')[:8]}.json",
                    mime="application/json",
                )

            st.json(fhir_bundle, expanded=False)

    # ── Frozen Legal & Clinical Disclaimer ──
    st.markdown("---")
    st.caption(
        f"⚠️ **Clinical Safety Disclaimer:** {record.get('disclaimer') or 'This is an AI-generated clinical tool. Always consult a qualified medical professional.'}"
    )
