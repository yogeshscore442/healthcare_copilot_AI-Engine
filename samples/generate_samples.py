"""
generate_samples.py — Generates 12 realistic synthetic medical documents and ground truth JSONs.
Uses Pillow for images and ReportLab for PDFs.
All patient data is purely synthetic and fictional.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

SAMPLES_DIR = Path(__file__).parent
GROUND_TRUTH_DIR = SAMPLES_DIR / "ground_truth"

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

DISCLAIMER = (
    "This is AI-generated information to help you understand your records. "
    "It is not a diagnosis or medical advice. Please consult your doctor."
)


def _get_font(size: int = 14, bold: bool = False):
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            return ImageFont.truetype(font_name, size)
        except Exception:
            return ImageFont.load_default()


def create_lab_image(filename: str, title: str, patient_info: dict, test_rows: list[dict]):
    """Creates a realistic clinical diagnostic laboratory report image."""
    img = Image.new("RGB", (900, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = _get_font(22, bold=True)
    f_header = _get_font(13, bold=True)
    f_text = _get_font(12, bold=False)
    f_sub = _get_font(10, bold=False)

    # Header banner
    draw.rectangle([(30, 30), (870, 100)], fill=(240, 245, 250), outline=(200, 215, 230), width=1)
    draw.text((50, 40), "APEX CLINICAL DIAGNOSTICS & PATHOLOGY LAB", fill=(20, 60, 120), font=f_title)
    draw.text((50, 72), "NABL Accredited Lab #MC-2041 | ISO 15189:2012 Certified | Ph: +91 44 2819 0000", fill=(80, 80, 80), font=f_sub)

    # Patient info box
    draw.rectangle([(30, 115), (870, 185)], fill=(250, 250, 250), outline=(220, 220, 220))
    draw.text((45, 125), f"Patient Name: {patient_info.get('name', 'N/A')}", fill=(0, 0, 0), font=f_text)
    draw.text((350, 125), f"Age / Sex: {patient_info.get('age', 'N/A')} / {patient_info.get('sex', 'N/A')}", fill=(0, 0, 0), font=f_text)
    draw.text((600, 125), f"UHID: {patient_info.get('uhid', 'N/A')}", fill=(0, 0, 0), font=f_text)
    draw.text((45, 155), f"Referred By: {patient_info.get('doctor', 'N/A')}", fill=(0, 0, 0), font=f_text)
    draw.text((350, 155), f"Collection Date: {patient_info.get('coll_date', 'N/A')}", fill=(0, 0, 0), font=f_text)
    draw.text((600, 155), f"Report Date: {patient_info.get('doc_date', 'N/A')}", fill=(0, 0, 0), font=f_text)

    # Section Title
    draw.text((30, 205), title.upper(), fill=(20, 60, 120), font=_get_font(16, bold=True))

    # Table Header
    y = 240
    draw.rectangle([(30, y), (870, y + 30)], fill=(230, 235, 245))
    draw.text((45, y + 7), "INVESTIGATION", fill=(0, 0, 0), font=f_header)
    draw.text((320, y + 7), "RESULT", fill=(0, 0, 0), font=f_header)
    draw.text((460, y + 7), "UNIT", fill=(0, 0, 0), font=f_header)
    draw.text((600, y + 7), "REFERENCE INTERVAL", fill=(0, 0, 0), font=f_header)

    y += 35
    for row in test_rows:
        draw.line([(30, y), (870, y)], fill=(235, 235, 235), width=1)
        name = row["name"]
        val_str = str(row["value"])
        unit = row.get("unit", "")
        ref = f"{row.get('ref_low', '')} - {row.get('ref_high', '')}" if row.get('ref_low') is not None else f"< {row.get('ref_high', '')}"
        
        is_abnormal = row.get("flag") in ("HIGH", "LOW")
        val_color = (200, 0, 0) if is_abnormal else (0, 0, 0)
        font_to_use = _get_font(12, bold=True) if is_abnormal else f_text

        draw.text((45, y + 6), name, fill=(0, 0, 0), font=f_text)
        draw.text((320, y + 6), val_str, fill=val_color, font=font_to_use)
        draw.text((460, y + 6), unit, fill=(60, 60, 60), font=f_text)
        draw.text((600, y + 6), ref, fill=(80, 80, 80), font=f_text)
        y += 32

    # Footer
    draw.line([(30, 1000), (870, 1000)], fill=(200, 200, 200), width=1)
    draw.text((45, 1015), "Pathologist: Dr. K. Ramanathan, MD (Path)", fill=(50, 50, 50), font=f_sub)
    draw.text((620, 1015), "** End of Laboratory Report **", fill=(100, 100, 100), font=f_sub)

    out_path = SAMPLES_DIR / filename
    img.save(out_path, "JPEG", quality=95)
    print(f"Generated {out_path}")


def create_prescription_image(filename: str, doc_name: str, clinic: str, patient_info: dict, meds: list[dict], diag: str = ""):
    """Creates a realistic clinic prescription image."""
    img = Image.new("RGB", (850, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_doc = _get_font(20, bold=True)
    f_spec = _get_font(12, bold=False)
    f_body = _get_font(13, bold=False)
    f_rx = _get_font(24, bold=True)
    f_bold = _get_font(13, bold=True)

    # Doctor letterhead
    draw.rectangle([(30, 25), (820, 115)], fill=(245, 250, 255), outline=(210, 225, 240))
    draw.text((45, 35), doc_name, fill=(10, 50, 110), font=f_doc)
    draw.text((45, 65), clinic, fill=(70, 70, 70), font=f_spec)
    draw.text((580, 40), f"Date: {patient_info.get('doc_date', '2026-03-15')}", fill=(50, 50, 50), font=f_body)

    # Patient Details bar
    draw.line([(30, 125), (820, 125)], fill=(180, 180, 180), width=1)
    draw.text((45, 135), f"Patient: {patient_info.get('name', 'Patient')}", fill=(0, 0, 0), font=f_body)
    draw.text((360, 135), f"Age: {patient_info.get('age', '45')} yrs   Sex: {patient_info.get('sex', 'M')}", fill=(0, 0, 0), font=f_body)
    draw.text((620, 135), f"Weight: {patient_info.get('weight', '68')} kg", fill=(0, 0, 0), font=f_body)
    draw.line([(30, 165), (820, 165)], fill=(180, 180, 180), width=1)

    y = 180
    if diag:
        draw.text((45, y), f"Clinical Impression / Diagnosis: {diag}", fill=(40, 40, 40), font=f_bold)
        y += 35

    draw.text((45, y), "Rx", fill=(10, 50, 110), font=f_rx)
    y += 45

    for i, med in enumerate(meds, 1):
        name_str = f"{i}. Tab. {med['name_raw']}" if not med['name_raw'].startswith(('Tab', 'Cap', 'Syp')) else f"{i}. {med['name_raw']}"
        draw.text((60, y), name_str, fill=(0, 0, 0), font=f_bold)
        
        sched = med.get('schedule_raw', '')
        food = med.get('food_instruction', '')
        food_txt = f"({food.replace('_', ' ')})" if food else ""
        dur = f"x {med['duration_days']} days" if med.get('duration_days') else ""
        detail = f"   Schedule: {sched}   {food_txt}   {dur}".strip()
        draw.text((60, y + 24), detail, fill=(50, 50, 50), font=f_body)
        y += 60

    # Follow up advice
    y = max(y + 30, 850)
    draw.rectangle([(45, y), (800, y + 70)], fill=(250, 250, 250), outline=(220, 220, 220))
    follow_up = patient_info.get("follow_up_date", "2026-03-30")
    draw.text((55, y + 15), f"Advice: Low salt diet, daily brisk walk 30 mins.", fill=(40, 40, 40), font=f_body)
    draw.text((55, y + 40), f"Review after 2 weeks / Follow-up Date: {follow_up}", fill=(20, 60, 120), font=f_bold)

    # Signature line
    draw.line([(600, 1020), (780, 1020)], fill=(100, 100, 100), width=1)
    draw.text((620, 1028), "Doctor Signature", fill=(80, 80, 80), font=f_spec)

    out_path = SAMPLES_DIR / filename
    img.save(out_path, "JPEG", quality=95)
    print(f"Generated {out_path}")


def create_discharge_pdf(filename: str, patient_info: dict, hospital: str, diag: str, course: str, meds: list[dict]):
    """Generates an inpatient hospital discharge summary PDF using ReportLab."""
    out_path = SAMPLES_DIR / filename
    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#0B3C5D"))
    c.drawString(50, height - 50, hospital)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(50, height - 70, "DEPARTMENT OF GENERAL MEDICINE - DISCHARGE SUMMARY")
    c.setLineWidth(1)
    c.setStrokeColor(colors.gray)
    c.line(50, height - 80, width - 50, height - 80)

    # Patient info
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 105, f"Patient Name: {patient_info['name']}")
    c.drawString(280, height - 105, f"Age/Sex: {patient_info['age']} / {patient_info['sex']}")
    c.drawString(450, height - 105, f"IP No: {patient_info['ip_no']}")

    c.drawString(50, height - 125, f"Admission Date: {patient_info['adm_date']}")
    c.drawString(280, height - 125, f"Discharge Date: {patient_info['doc_date']}")
    c.drawString(450, height - 125, f"Consultant: {patient_info['doctor']}")
    c.line(50, height - 135, width - 50, height - 135)

    # Diagnosis & Course
    y = height - 160
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#0B3C5D"))
    c.drawString(50, y, "FINAL DIAGNOSIS:")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(170, y, diag)
    y -= 30

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#0B3C5D"))
    c.drawString(50, y, "HOSPITAL COURSE & CLINICAL SUMMARY:")
    y -= 18
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    for line in course.split("\n"):
        c.drawString(50, y, line)
        y -= 14

    y -= 15
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#0B3C5D"))
    c.drawString(50, y, "DISCHARGE MEDICATIONS:")
    y -= 20

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#333333"))
    c.drawString(60, y, "MEDICINE")
    c.drawString(240, y, "DOSAGE / SCHEDULE")
    c.drawString(420, y, "DURATION")
    y -= 12
    c.line(50, y + 4, width - 50, y + 4)

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    for med in meds:
        c.drawString(60, y, med["name_raw"])
        c.drawString(240, y, f"{med.get('schedule_raw', '')} ({med.get('food_instruction', '')})")
        c.drawString(420, y, f"{med.get('duration_days', '')} days")
        y -= 20

    y -= 25
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"FOLLOW-UP APPOINTMENT: {patient_info['follow_up_date']} in OPD")
    y -= 16
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Review with blood investigation reports. In case of emergency report to casualty.")

    c.line(400, 70, 550, 70)
    c.drawString(420, 55, "Authorized Signatory")

    c.save()
    print(f"Generated {out_path}")


def create_tamil_mixed_image(filename: str):
    """Creates a bilingual Tamil-English clinic prescription."""
    img = Image.new("RGB", (850, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = _get_font(20, bold=True)
    f_bold = _get_font(13, bold=True)
    f_body = _get_font(12, bold=False)

    draw.rectangle([(30, 30), (820, 120)], fill=(245, 252, 245), outline=(200, 230, 200))
    draw.text((50, 40), "Dr. S. MURUGAN, MBBS, MD", fill=(10, 80, 40), font=f_title)
    draw.text((50, 70), "Family Physician & Diabetologist | குடும்ப மருத்துவர்", fill=(60, 60, 60), font=f_body)
    draw.text((50, 92), "Chennai Health Center | சென்னை சுகாதார மையம்", fill=(80, 80, 80), font=f_body)
    draw.text((620, 45), "Date: 2026-03-12", fill=(40, 40, 40), font=f_bold)

    draw.rectangle([(30, 130), (820, 180)], fill=(250, 250, 250), outline=(220, 220, 220))
    draw.text((45, 145), "Patient: Karthik R (கார்த்திக்)   Age: 52 / M   UHID: CHC-9921", fill=(0, 0, 0), font=f_body)

    draw.text((45, 200), "Diagnosis / மருத்துவ நிலை: Type 2 Diabetes / சர்க்கரை நோய், Hypertension", fill=(20, 20, 20), font=f_bold)
    draw.text((45, 235), "Rx (மருந்து பரிந்துரை):", fill=(10, 80, 40), font=_get_font(18, bold=True))

    meds = [
        ("1. Tab. Glycomet 500 (Metformin 500mg)", "1-0-1 (காலை 1 இரவு 1) - உணவுக்குப் பின் (after food) x 30 days"),
        ("2. Tab. Telma 40 (Telmisartan 40mg)", "1-0-0 (காலை 1) - உணவுக்கு முன் (before food) x 30 days"),
        ("3. Tab. Atorlip 10 (Atorvastatin 10mg)", "0-0-1 (இரவு 1 HS) - இரவு தூங்கும் முன் (after food) x 30 days"),
    ]

    y = 275
    for title_txt, inst_txt in meds:
        draw.text((60, y), title_txt, fill=(0, 0, 0), font=f_bold)
        draw.text((60, y + 24), inst_txt, fill=(50, 50, 50), font=f_body)
        y += 65

    draw.rectangle([(45, 800), (800, 870)], fill=(250, 250, 250), outline=(220, 220, 220))
    draw.text((55, 815), "அடுத்த பரிசோதனை தேதி (Follow-up Date): 2026-04-12", fill=(10, 80, 40), font=f_bold)
    draw.text((55, 840), "ரத்த சர்க்கரை சோதனை (FBS/PPBS) செய்து வரவும்.", fill=(40, 40, 40), font=f_body)

    out_path = SAMPLES_DIR / filename
    img.save(out_path, "JPEG", quality=95)
    print(f"Generated {out_path}")


def create_handwritten_image(filename: str):
    """Creates a simulated doctor prescription with handwriting-style appearance."""
    img = Image.new("RGB", (850, 1100), color=(252, 250, 245))
    draw = ImageDraw.Draw(img)

    f_title = _get_font(18, bold=True)
    f_body = _get_font(13, bold=False)
    f_bold = _get_font(13, bold=True)

    # Letterhead
    draw.text((45, 35), "CITY CARE CLINIC - DR. ANAND RAO, MD", fill=(50, 50, 80), font=f_title)
    draw.text((45, 62), "[SIMULATED CLINICAL DOCUMENT FOR AI EVALUATION]", fill=(180, 50, 50), font=_get_font(11, bold=True))
    draw.text((640, 35), "Date: 2026-03-20", fill=(50, 50, 50), font=f_body)
    draw.line([(30, 85), (820, 85)], fill=(200, 200, 200), width=1)

    draw.text((45, 100), "Pt: Suresh Kumar | 38y/M | BP: 120/80 | Wt: 72kg", fill=(0, 0, 0), font=f_body)
    draw.text((45, 130), "Dx: Acute Bronchitis / URTI", fill=(0, 0, 0), font=f_bold)
    draw.text((45, 170), "Rx", fill=(30, 30, 100), font=_get_font(24, bold=True))

    items = [
        ("Tab. Augmentin 625mg", "1-0-1  after food  x 5 days"),
        ("Tab. Dolo 650mg", "1-0-1  SOS for fever / bodyache"),
        ("Cap. Pan-D", "1-0-0  before food  x 5 days"),
        ("Tab. Cetirizine 10mg", "0-0-1  at night  x 5 days"),
    ]

    y = 220
    for med, sch in items:
        draw.text((70, y), f"- {med}", fill=(10, 10, 50), font=f_bold)
        draw.text((95, y + 25), sch, fill=(40, 40, 40), font=f_body)
        y += 65

    draw.text((45, 850), "Advise: Steam inhalation BD, warm water fluids.", fill=(0, 0, 0), font=f_body)
    draw.text((45, 880), "Review after 5 days if cough persists. Follow-up: 2026-03-25", fill=(10, 50, 110), font=f_bold)

    out_path = SAMPLES_DIR / filename
    img.save(out_path, "JPEG", quality=95)
    print(f"Generated {out_path}")


def create_diagnostic_image(filename: str):
    """Creates a text-based Chest X-Ray radiology report image."""
    img = Image.new("RGB", (850, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = _get_font(20, bold=True)
    f_head = _get_font(13, bold=True)
    f_body = _get_font(12, bold=False)

    draw.rectangle([(30, 30), (820, 100)], fill=(240, 245, 250), outline=(200, 215, 230))
    draw.text((50, 40), "CITY RADIOLOGY & IMAGING INSTITUTE", fill=(15, 50, 100), font=f_title)
    draw.text((50, 70), "Department of Radiodiagnosis | 128 Slice CT | 3T MRI | Digital X-Ray", fill=(80, 80, 80), font=f_body)

    draw.rectangle([(30, 115), (820, 175)], fill=(250, 250, 250), outline=(220, 220, 220))
    draw.text((45, 125), "Patient: Rajesh Verma   Age/Sex: 48 / M   Date: 2026-03-18", fill=(0, 0, 0), font=f_body)
    draw.text((45, 148), "Referred By: Dr. P. Mehta   Investigation: CHEST X-RAY PA VIEW", fill=(0, 0, 0), font=f_head)

    draw.text((45, 210), "CLINICAL INDICATION: Persistent cough and fever for 1 week.", fill=(0, 0, 0), font=f_body)

    draw.text((45, 260), "FINDINGS:", fill=(15, 50, 100), font=f_head)
    findings = (
        "- Trachea is centrally located.\n"
        "- Cardiac silhouette is within normal limits for size and configuration.\n"
        "- Mediastinal and hilar contours appear normal.\n"
        "- Both lung fields are clear; no focal consolidation, pleural effusion, or pneumothorax.\n"
        "- Both costophrenic angles and hemidiaphragms are sharp and well-defined.\n"
        "- Visualized bony thorax and soft tissues show no significant abnormality."
    )
    y = 290
    for line in findings.split("\n"):
        draw.text((55, y), line, fill=(30, 30, 30), font=f_body)
        y += 24

    draw.text((45, y + 30), "IMPRESSION:", fill=(15, 50, 100), font=f_head)
    draw.text((55, y + 60), "Normal chest radiograph (PA View). No active cardiopulmonary disease detected.", fill=(0, 0, 0), font=_get_font(12, bold=True))

    draw.text((45, 950), "Radiologist: Dr. Sunita Rao, MD (Radiology)", fill=(60, 60, 60), font=f_body)

    out_path = SAMPLES_DIR / filename
    img.save(out_path, "JPEG", quality=95)
    print(f"Generated {out_path}")


def main():
    print("Generating 12 synthetic medical sample files...")

    # 1. lab1.jpg - Complete Blood Count (CBC)
    lab1_tests = [
        {"name": "Haemoglobin", "value": 10.2, "unit": "g/dL", "ref_low": 13.5, "ref_high": 17.5, "flag": "LOW"},
        {"name": "WBC", "value": 12.8, "unit": "10³/µL", "ref_low": 4.0, "ref_high": 11.0, "flag": "HIGH"},
        {"name": "Platelets", "value": 240.0, "unit": "10³/µL", "ref_low": 150.0, "ref_high": 400.0, "flag": "NORMAL"},
        {"name": "RBC", "value": 4.1, "unit": "10⁶/µL", "ref_low": 4.5, "ref_high": 5.9, "flag": "LOW"},
        {"name": "Hematocrit", "value": 32.5, "unit": "%", "ref_low": 38.0, "ref_high": 50.0, "flag": "LOW"},
    ]
    create_lab_image(
        "lab1.jpg",
        "COMPLETE BLOOD COUNT (CBC)",
        {"name": "Venkatesh S", "age": 42, "sex": "M", "uhid": "LAB-1029", "doctor": "Dr. Ramesh MD", "coll_date": "2026-03-10", "doc_date": "2026-03-10"},
        lab1_tests
    )

    # 2. lab2.jpg - Lipid Profile
    lab2_tests = [
        {"name": "Total Cholesterol", "value": 248.0, "unit": "mg/dL", "ref_low": None, "ref_high": 200.0, "flag": "HIGH"},
        {"name": "Triglycerides", "value": 210.0, "unit": "mg/dL", "ref_low": None, "ref_high": 150.0, "flag": "HIGH"},
        {"name": "HDL", "value": 36.0, "unit": "mg/dL", "ref_low": 40.0, "ref_high": None, "flag": "LOW"},
        {"name": "LDL", "value": 165.0, "unit": "mg/dL", "ref_low": None, "ref_high": 100.0, "flag": "HIGH"},
    ]
    create_lab_image(
        "lab2.jpg",
        "LIPID PROFILE PANEL",
        {"name": "Arun Kumar", "age": 55, "sex": "M", "uhid": "LAB-2281", "doctor": "Dr. Priya MD", "coll_date": "2026-03-12", "doc_date": "2026-03-12"},
        lab2_tests
    )

    # 3. lab3.jpg - Diabetic Evaluation
    lab3_tests = [
        {"name": "Fasting Glucose", "value": 142.0, "unit": "mg/dL", "ref_low": 70.0, "ref_high": 100.0, "flag": "HIGH"},
        {"name": "HbA1c", "value": 8.4, "unit": "%", "ref_low": 4.0, "ref_high": 5.6, "flag": "HIGH"},
        {"name": "Random Glucose", "value": 220.0, "unit": "mg/dL", "ref_low": 70.0, "ref_high": 140.0, "flag": "HIGH"},
    ]
    create_lab_image(
        "lab3.jpg",
        "DIABETIC PROFILE REPORT",
        {"name": "Meenakshi Sundaram", "age": 60, "sex": "F", "uhid": "LAB-3094", "doctor": "Dr. G. Krishnan", "coll_date": "2026-03-14", "doc_date": "2026-03-14"},
        lab3_tests
    )

    # 4. lab4.jpg - Renal & Thyroid
    lab4_tests = [
        {"name": "Creatinine", "value": 1.6, "unit": "mg/dL", "ref_low": 0.6, "ref_high": 1.2, "flag": "HIGH"},
        {"name": "Urea", "value": 38.0, "unit": "mg/dL", "ref_low": 7.0, "ref_high": 20.0, "flag": "HIGH"},
        {"name": "TSH", "value": 6.8, "unit": "mIU/L", "ref_low": 0.4, "ref_high": 4.0, "flag": "HIGH"},
        {"name": "Sodium", "value": 139.0, "unit": "mEq/L", "ref_low": 136.0, "ref_high": 145.0, "flag": "NORMAL"},
        {"name": "Potassium", "value": 4.3, "unit": "mEq/L", "ref_low": 3.5, "ref_high": 5.1, "flag": "NORMAL"},
    ]
    create_lab_image(
        "lab4.jpg",
        "RENAL & THYROID EVALUATION",
        {"name": "Lakshmi Narayanan", "age": 67, "sex": "F", "uhid": "LAB-4120", "doctor": "Dr. V. Swaminathan", "coll_date": "2026-03-15", "doc_date": "2026-03-15"},
        lab4_tests
    )

    # 5. prescription1.jpg - Adult Hypertension & Diabetes
    p1_meds = [
        {"name_raw": "Telma 40", "generic": "Telmisartan", "strength": "40 mg", "schedule_raw": "1-0-0 before food", "schedule_parsed": ["morning"], "food_instruction": "before_food", "duration_days": 30, "confidence": 0.95},
        {"name_raw": "Glycomet 500", "generic": "Metformin", "strength": "500 mg", "schedule_raw": "1-0-1 after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 30, "confidence": 0.95},
        {"name_raw": "Atorlip 10", "generic": "Atorvastatin", "strength": "10 mg", "schedule_raw": "0-0-1 HS", "schedule_parsed": ["night"], "food_instruction": "after_food", "duration_days": 30, "confidence": 0.95},
    ]
    create_prescription_image(
        "prescription1.jpg",
        "Dr. S. K. VERMA, MD (General Medicine)",
        "City Heart & Diabetes Center, Ph: 044-24351234",
        {"name": "Ravi Chandran", "age": 50, "sex": "M", "weight": "74", "doc_date": "2026-03-15", "follow_up_date": "2026-04-15"},
        p1_meds,
        diag="Essential Hypertension, Type 2 Diabetes"
    )

    # 6. prescription2.jpg - Multi-med acute illness
    p2_meds = [
        {"name_raw": "Augmentin 625", "generic": "Amoxicillin + Clavulanate", "strength": "500 mg + 125 mg", "schedule_raw": "1-0-1 after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 5, "confidence": 0.95},
        {"name_raw": "Pan-D", "generic": "Pantoprazole + Domperidone", "strength": "40 mg + 10 mg", "schedule_raw": "1-0-0 before food", "schedule_parsed": ["morning"], "food_instruction": "before_food", "duration_days": 5, "confidence": 0.95},
        {"name_raw": "Dolo 650", "generic": "Paracetamol", "strength": "650 mg", "schedule_raw": "1-0-1 after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 3, "confidence": 0.95},
        {"name_raw": "Cetirizine 10", "generic": "Cetirizine", "strength": "10 mg", "schedule_raw": "0-0-1 at night", "schedule_parsed": ["night"], "food_instruction": None, "duration_days": 5, "confidence": 0.95},
    ]
    create_prescription_image(
        "prescription2.jpg",
        "Dr. N. ANITHA, MBBS, DNB (Fam. Med)",
        "Community Health Clinic, Kilpauk",
        {"name": "Pooja Sharma", "age": 28, "sex": "F", "weight": "55", "doc_date": "2026-03-18", "follow_up_date": "2026-03-23"},
        p2_meds,
        diag="Acute Upper Respiratory Tract Infection"
    )

    # 7. prescription3.jpg - Pediatric prescription
    p3_meds = [
        {"name_raw": "Calpol 120", "generic": "Paracetamol", "strength": "120 mg/5ml", "schedule_raw": "5ml TDS SOS", "schedule_parsed": ["morning", "afternoon", "night"], "food_instruction": "after_food", "duration_days": 3, "confidence": 0.90},
        {"name_raw": "Meftal-P", "generic": "Mefenamic Acid", "strength": "100 mg/5ml", "schedule_raw": "4ml BD after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 3, "confidence": 0.90},
        {"name_raw": "Vizylac", "generic": "Lactic Acid Bacillus + B Complex", "strength": None, "schedule_raw": "1 sachet OD in water", "schedule_parsed": ["morning"], "food_instruction": None, "duration_days": 5, "confidence": 0.90},
    ]
    create_prescription_image(
        "prescription3.jpg",
        "Dr. M. GOWRI, MD (Pediatrics)",
        "Apollo Children's Care, Chennai",
        {"name": "Master Aadhavan", "age": 4, "sex": "M", "weight": "16", "doc_date": "2026-03-20", "follow_up_date": "2026-03-24"},
        p3_meds,
        diag="Viral Pyrexia with Mild Dehydration"
    )

    # 8. discharge1.pdf - Acute Gastroenteritis Inpatient
    d1_meds = [
        {"name_raw": "Rablet 20", "generic": "Rabeprazole", "strength": "20 mg", "schedule_raw": "1-0-0 before food", "schedule_parsed": ["morning"], "food_instruction": "before_food", "duration_days": 14},
        {"name_raw": "Ondem 4", "generic": "Ondansetron", "strength": "4 mg", "schedule_raw": "1-0-1 before food", "schedule_parsed": ["morning", "night"], "food_instruction": "before_food", "duration_days": 3},
        {"name_raw": "Sporlac", "generic": "Lactobacillus Sporogenes", "strength": None, "schedule_raw": "1-0-1 after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 7},
    ]
    create_discharge_pdf(
        "discharge1.pdf",
        {"name": "Deepak Balakrishnan", "age": "34", "sex": "M", "ip_no": "IP-77821", "adm_date": "2026-03-08", "doc_date": "2026-03-11", "doctor": "Dr. V. Balasubramanian, MD", "follow_up_date": "2026-03-18"},
        "SIMS MULTISPECIALTY HOSPITAL, CHENNAI",
        "Acute Infectious Gastroenteritis with Moderate Dehydration (A09)",
        "Patient presented with frequent vomiting, watery diarrhea, and mild fever for 24 hours.\n"
        "Managed with IV fluids (Ringer Lactate), IV Ondansetron, and oral rehydration therapy.\n"
        "Vitals stabilized, oral feeds tolerated well. Discharged in stable condition.",
        d1_meds
    )

    # 9. discharge2.pdf - Laparoscopic Appendectomy
    d2_meds = [
        {"name_raw": "Zifi 200", "generic": "Cefixime", "strength": "200 mg", "schedule_raw": "1-0-1 after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 5},
        {"name_raw": "Combiflam", "generic": "Ibuprofen + Paracetamol", "strength": "400 mg + 325 mg", "schedule_raw": "1-0-1 after food", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 5},
        {"name_raw": "Pan-D", "generic": "Pantoprazole + Domperidone", "strength": "40 mg + 10 mg", "schedule_raw": "1-0-0 before food", "schedule_parsed": ["morning"], "food_instruction": "before_food", "duration_days": 7},
    ]
    create_discharge_pdf(
        "discharge2.pdf",
        {"name": "Sanjay Madhav", "age": "26", "sex": "M", "ip_no": "SURG-90214", "adm_date": "2026-03-14", "doc_date": "2026-03-16", "doctor": "Dr. C. Natarajan, MS (Gen. Surg)", "follow_up_date": "2026-03-23"},
        "FORTIS MALAR HOSPITAL, CHENNAI",
        "Acute Appendicitis - Post Laparoscopic Appendectomy (K35.80)",
        "Underwent uncomplicated Laparoscopic Appendectomy on 2026-03-14 under general anesthesia.\n"
        "Post-operative recovery smooth. Port site dressings intact and clean. Ambulatory and tolerating soft diet.",
        d2_meds
    )

    # 10. tamil_mixed1.jpg
    create_tamil_mixed_image("tamil_mixed1.jpg")

    # 11. handwritten1.jpg
    create_handwritten_image("handwritten1.jpg")

    # 12. diagnostic1.jpg
    create_diagnostic_image("diagnostic1.jpg")

    # Now generate ground truth files for all 12 samples
    generate_ground_truths(lab1_tests, lab2_tests, lab3_tests, lab4_tests, p1_meds, p2_meds, p3_meds, d1_meds, d2_meds)


def generate_ground_truths(lab1_tests, lab2_tests, lab3_tests, lab4_tests, p1_meds, p2_meds, p3_meds, d1_meds, d2_meds):
    """Write contract-compliant ground truth JSON for all 12 samples."""
    print("Writing ground truth JSON files...")

    # helper to clean tests
    def format_tests(t_list):
        return [
            {
                "name": t["name"],
                "loinc": t.get("loinc"),
                "value": t.get("value"),
                "value_text": t.get("value_text"),
                "unit": t.get("unit"),
                "ref_low": t.get("ref_low"),
                "ref_high": t.get("ref_high"),
                "flag": t.get("flag", "UNKNOWN"),
                "explanation_en": None,
                "explanation_ta": None,
                "confidence": 1.0,
                "bbox": None
            }
            for t in t_list
        ]

    # helper to clean meds
    def format_meds(m_list):
        return [
            {
                "name_raw": m["name_raw"],
                "generic": m.get("generic"),
                "strength": m.get("strength"),
                "schedule_raw": m.get("schedule_raw"),
                "schedule_parsed": m.get("schedule_parsed", []),
                "food_instruction": m.get("food_instruction"),
                "duration_days": m.get("duration_days"),
                "confidence": 1.0,
                "bbox": None
            }
            for m in m_list
        ]

    # 1. lab1
    gt_lab1 = {
        "doc_type": "lab_report",
        "doc_date": "2026-03-10",
        "collection_date": "2026-03-10",
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [],
        "tests": format_tests(lab1_tests),
        "diagnoses": [],
        "needs_review": ["tests[0]", "tests[1]", "tests[3]", "tests[4]"],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "lab1.json", "w", encoding="utf-8") as f:
        json.dump(gt_lab1, f, indent=2)

    # 2. lab2
    gt_lab2 = {
        "doc_type": "lab_report",
        "doc_date": "2026-03-12",
        "collection_date": "2026-03-12",
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [],
        "tests": format_tests(lab2_tests),
        "diagnoses": [],
        "needs_review": ["tests[0]", "tests[1]", "tests[2]", "tests[3]"],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "lab2.json", "w", encoding="utf-8") as f:
        json.dump(gt_lab2, f, indent=2)

    # 3. lab3
    gt_lab3 = {
        "doc_type": "lab_report",
        "doc_date": "2026-03-14",
        "collection_date": "2026-03-14",
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [],
        "tests": format_tests(lab3_tests),
        "diagnoses": [],
        "needs_review": ["tests[0]", "tests[1]", "tests[2]"],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "lab3.json", "w", encoding="utf-8") as f:
        json.dump(gt_lab3, f, indent=2)

    # 4. lab4
    gt_lab4 = {
        "doc_type": "lab_report",
        "doc_date": "2026-03-15",
        "collection_date": "2026-03-15",
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [],
        "tests": format_tests(lab4_tests),
        "diagnoses": [],
        "needs_review": ["tests[0]", "tests[1]", "tests[2]"],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "lab4.json", "w", encoding="utf-8") as f:
        json.dump(gt_lab4, f, indent=2)

    # 5. prescription1
    gt_p1 = {
        "doc_type": "prescription",
        "doc_date": "2026-03-15",
        "collection_date": None,
        "follow_up_date": "2026-04-15",
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": format_meds(p1_meds),
        "tests": [],
        "diagnoses": [
            {"text": "Essential Hypertension", "confidence": 1.0, "icd10": "I10"},
            {"text": "Type 2 Diabetes", "confidence": 1.0, "icd10": "E11.9"}
        ],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "prescription1.json", "w", encoding="utf-8") as f:
        json.dump(gt_p1, f, indent=2)

    # 6. prescription2
    gt_p2 = {
        "doc_type": "prescription",
        "doc_date": "2026-03-18",
        "collection_date": None,
        "follow_up_date": "2026-03-23",
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": format_meds(p2_meds),
        "tests": [],
        "diagnoses": [{"text": "Acute Upper Respiratory Tract Infection", "confidence": 1.0, "icd10": "J06.9"}],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "prescription2.json", "w", encoding="utf-8") as f:
        json.dump(gt_p2, f, indent=2)

    # 7. prescription3
    gt_p3 = {
        "doc_type": "prescription",
        "doc_date": "2026-03-20",
        "collection_date": None,
        "follow_up_date": "2026-03-24",
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": format_meds(p3_meds),
        "tests": [],
        "diagnoses": [{"text": "Viral Pyrexia with Mild Dehydration", "confidence": 1.0, "icd10": None}],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "prescription3.json", "w", encoding="utf-8") as f:
        json.dump(gt_p3, f, indent=2)

    # 8. discharge1
    gt_d1 = {
        "doc_type": "discharge_summary",
        "doc_date": "2026-03-11",
        "collection_date": None,
        "follow_up_date": "2026-03-18",
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": format_meds(d1_meds),
        "tests": [],
        "diagnoses": [{"text": "Acute Infectious Gastroenteritis with Moderate Dehydration", "confidence": 1.0, "icd10": "A09"}],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "discharge1.json", "w", encoding="utf-8") as f:
        json.dump(gt_d1, f, indent=2)

    # 9. discharge2
    gt_d2 = {
        "doc_type": "discharge_summary",
        "doc_date": "2026-03-16",
        "collection_date": None,
        "follow_up_date": "2026-03-23",
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": format_meds(d2_meds),
        "tests": [],
        "diagnoses": [{"text": "Acute Appendicitis - Post Laparoscopic Appendectomy", "confidence": 1.0, "icd10": "K35.80"}],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "discharge2.json", "w", encoding="utf-8") as f:
        json.dump(gt_d2, f, indent=2)

    # 10. tamil_mixed1
    gt_tm = {
        "doc_type": "prescription",
        "doc_date": "2026-03-12",
        "collection_date": None,
        "follow_up_date": "2026-04-12",
        "language": "mixed",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [
            {"name_raw": "Glycomet 500", "generic": "Metformin", "strength": "500 mg", "schedule_raw": "1-0-1", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 30, "confidence": 1.0, "bbox": None},
            {"name_raw": "Telma 40", "generic": "Telmisartan", "strength": "40 mg", "schedule_raw": "1-0-0", "schedule_parsed": ["morning"], "food_instruction": "before_food", "duration_days": 30, "confidence": 1.0, "bbox": None},
            {"name_raw": "Atorlip 10", "generic": "Atorvastatin", "strength": "10 mg", "schedule_raw": "0-0-1", "schedule_parsed": ["night"], "food_instruction": "after_food", "duration_days": 30, "confidence": 1.0, "bbox": None}
        ],
        "tests": [],
        "diagnoses": [
            {"text": "Type 2 Diabetes", "confidence": 1.0, "icd10": "E11.9"},
            {"text": "Hypertension", "confidence": 1.0, "icd10": "I10"}
        ],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "tamil_mixed1.json", "w", encoding="utf-8") as f:
        json.dump(gt_tm, f, indent=2)

    # 11. handwritten1
    gt_hw = {
        "doc_type": "prescription",
        "doc_date": "2026-03-20",
        "collection_date": None,
        "follow_up_date": "2026-03-25",
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [
            {"name_raw": "Augmentin 625mg", "generic": "Amoxicillin + Clavulanate", "strength": "500 mg + 125 mg", "schedule_raw": "1-0-1 after food x 5 days", "schedule_parsed": ["morning", "night"], "food_instruction": "after_food", "duration_days": 5, "confidence": 1.0, "bbox": None},
            {"name_raw": "Dolo 650mg", "generic": "Paracetamol", "strength": "650 mg", "schedule_raw": "1-0-1 SOS for fever", "schedule_parsed": ["morning", "night"], "food_instruction": None, "duration_days": None, "confidence": 1.0, "bbox": None},
            {"name_raw": "Pan-D", "generic": "Pantoprazole + Domperidone", "strength": "40 mg + 10 mg", "schedule_raw": "1-0-0 before food x 5 days", "schedule_parsed": ["morning"], "food_instruction": "before_food", "duration_days": 5, "confidence": 1.0, "bbox": None},
            {"name_raw": "Cetirizine 10mg", "generic": "Cetirizine", "strength": "10 mg", "schedule_raw": "0-0-1 at night x 5 days", "schedule_parsed": ["night"], "food_instruction": None, "duration_days": 5, "confidence": 1.0, "bbox": None}
        ],
        "tests": [],
        "diagnoses": [{"text": "Acute Bronchitis", "confidence": 1.0, "icd10": "J20.9"}],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "handwritten1.json", "w", encoding="utf-8") as f:
        json.dump(gt_hw, f, indent=2)

    # 12. diagnostic1
    gt_diag1 = {
        "doc_type": "diagnostic_report",
        "doc_date": "2026-03-18",
        "collection_date": None,
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": True,
        "allergies": [],
        "medicines": [],
        "tests": [
            {
                "name": "Chest X-Ray PA View",
                "loinc": None,
                "value": None,
                "value_text": "Normal chest radiograph (PA View). No active cardiopulmonary disease detected.",
                "unit": None,
                "ref_low": None,
                "ref_high": None,
                "flag": "NORMAL",
                "explanation_en": None,
                "explanation_ta": None,
                "confidence": 1.0,
                "bbox": None
            }
        ],
        "diagnoses": [],
        "needs_review": [],
        "disclaimer": DISCLAIMER,
        "error": None
    }
    with open(GROUND_TRUTH_DIR / "diagnostic1.json", "w", encoding="utf-8") as f:
        json.dump(gt_diag1, f, indent=2)

    print("All 12 ground truth files successfully generated!")


if __name__ == "__main__":
    main()
