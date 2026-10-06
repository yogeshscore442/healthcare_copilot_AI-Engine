"""
expand_data.py — Expands all training/knowledge-base data files.
Run once: python expand_data.py
"""
import json, csv, os

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── 1. Expand icd10.json ──────────────────────────────────────────────────────
ICD10_PATH = os.path.join(ROOT, "ai_engine", "icd10.json")

icd10_extra = {
    "type 1 diabetes": {"icd10": "E10.9", "display": "Type 1 diabetes mellitus without complications", "category": "Endocrinology"},
    "t1dm": {"icd10": "E10.9", "display": "Type 1 diabetes mellitus", "category": "Endocrinology"},
    "diabetic nephropathy": {"icd10": "E11.65", "display": "Type 2 diabetes mellitus with hyperglycemia", "category": "Endocrinology"},
    "diabetic neuropathy": {"icd10": "E11.40", "display": "Type 2 diabetes mellitus with diabetic neuropathy, unspecified", "category": "Endocrinology"},
    "diabetic retinopathy": {"icd10": "E11.319", "display": "Type 2 diabetes mellitus with unspecified diabetic retinopathy", "category": "Endocrinology"},
    "hypoglycemia": {"icd10": "E16.0", "display": "Drug-induced hypoglycemia without coma", "category": "Endocrinology"},
    "metabolic syndrome": {"icd10": "E88.81", "display": "Metabolic syndrome", "category": "Endocrinology"},
    "obesity": {"icd10": "E66.9", "display": "Obesity, unspecified", "category": "Endocrinology"},
    "morbid obesity": {"icd10": "E66.01", "display": "Morbid (severe) obesity due to excess calories", "category": "Endocrinology"},
    "hypertensive heart disease": {"icd10": "I11.9", "display": "Hypertensive heart disease without heart failure", "category": "Cardiology"},
    "mixed dyslipidemia": {"icd10": "E78.2", "display": "Mixed hyperlipidemia", "category": "Cardiology"},
    "acute myocardial infarction": {"icd10": "I21.9", "display": "Acute myocardial infarction, unspecified", "category": "Cardiology"},
    "mi": {"icd10": "I21.9", "display": "Acute myocardial infarction, unspecified", "category": "Cardiology"},
    "heart attack": {"icd10": "I21.9", "display": "Acute myocardial infarction, unspecified", "category": "Cardiology"},
    "angina pectoris": {"icd10": "I20.9", "display": "Angina pectoris, unspecified", "category": "Cardiology"},
    "unstable angina": {"icd10": "I20.0", "display": "Unstable angina", "category": "Cardiology"},
    "heart failure": {"icd10": "I50.9", "display": "Heart failure, unspecified", "category": "Cardiology"},
    "congestive heart failure": {"icd10": "I50.9", "display": "Heart failure, unspecified", "category": "Cardiology"},
    "chf": {"icd10": "I50.9", "display": "Heart failure, unspecified", "category": "Cardiology"},
    "atrial fibrillation": {"icd10": "I48.91", "display": "Unspecified atrial fibrillation", "category": "Cardiology"},
    "af": {"icd10": "I48.91", "display": "Unspecified atrial fibrillation", "category": "Cardiology"},
    "stroke": {"icd10": "I63.9", "display": "Cerebral infarction, unspecified", "category": "Neurology"},
    "cerebral infarction": {"icd10": "I63.9", "display": "Cerebral infarction, unspecified", "category": "Neurology"},
    "ischemic stroke": {"icd10": "I63.9", "display": "Cerebral infarction, unspecified", "category": "Neurology"},
    "tia": {"icd10": "G45.9", "display": "Transient cerebral ischaemic attack, unspecified", "category": "Neurology"},
    "transient ischemic attack": {"icd10": "G45.9", "display": "Transient cerebral ischaemic attack, unspecified", "category": "Neurology"},
    "epilepsy": {"icd10": "G40.909", "display": "Epilepsy, unspecified, not intractable, without status epilepticus", "category": "Neurology"},
    "seizure disorder": {"icd10": "G40.909", "display": "Epilepsy, unspecified, not intractable", "category": "Neurology"},
    "migraine": {"icd10": "G43.909", "display": "Migraine, unspecified, not intractable, without status migrainosus", "category": "Neurology"},
    "parkinson disease": {"icd10": "G20", "display": "Parkinson's disease", "category": "Neurology"},
    "parkinson's disease": {"icd10": "G20", "display": "Parkinson's disease", "category": "Neurology"},
    "alzheimer disease": {"icd10": "G30.9", "display": "Alzheimer's disease, unspecified", "category": "Neurology"},
    "dementia": {"icd10": "F03.90", "display": "Unspecified dementia without behavioral disturbance", "category": "Neurology"},
    "peripheral neuropathy": {"icd10": "G62.9", "display": "Polyneuropathy, unspecified", "category": "Neurology"},
    "hyperthyroidism": {"icd10": "E05.90", "display": "Thyrotoxicosis, unspecified, without thyrotoxic crisis or storm", "category": "Endocrinology"},
    "graves disease": {"icd10": "E05.00", "display": "Thyrotoxicosis with diffuse goiter without thyrotoxic crisis", "category": "Endocrinology"},
    "goiter": {"icd10": "E04.9", "display": "Nontoxic goiter, unspecified", "category": "Endocrinology"},
    "gastroesophageal reflux": {"icd10": "K21.9", "display": "Gastro-esophageal reflux disease without esophagitis", "category": "Gastroenterology"},
    "peptic ulcer disease": {"icd10": "K27.9", "display": "Peptic ulcer, site unspecified, without haemorrhage or perforation", "category": "Gastroenterology"},
    "pud": {"icd10": "K27.9", "display": "Peptic ulcer, site unspecified, without haemorrhage or perforation", "category": "Gastroenterology"},
    "gastric ulcer": {"icd10": "K25.9", "display": "Gastric ulcer, unspecified as acute or chronic", "category": "Gastroenterology"},
    "irritable bowel syndrome": {"icd10": "K58.9", "display": "Irritable bowel syndrome without diarrhoea", "category": "Gastroenterology"},
    "ibs": {"icd10": "K58.9", "display": "Irritable bowel syndrome without diarrhoea", "category": "Gastroenterology"},
    "inflammatory bowel disease": {"icd10": "K51.90", "display": "Ulcerative colitis, unspecified, without complications", "category": "Gastroenterology"},
    "crohn disease": {"icd10": "K50.90", "display": "Crohn's disease of small intestine without complications", "category": "Gastroenterology"},
    "ulcerative colitis": {"icd10": "K51.90", "display": "Ulcerative colitis, unspecified, without complications", "category": "Gastroenterology"},
    "liver cirrhosis": {"icd10": "K74.60", "display": "Unspecified cirrhosis of liver", "category": "Hepatology"},
    "cirrhosis": {"icd10": "K74.60", "display": "Unspecified cirrhosis of liver", "category": "Hepatology"},
    "hepatitis b": {"icd10": "B18.1", "display": "Chronic viral hepatitis B without delta-agent", "category": "Hepatology"},
    "hepatitis c": {"icd10": "B18.2", "display": "Chronic viral hepatitis C", "category": "Hepatology"},
    "fatty liver": {"icd10": "K76.0", "display": "Fatty (change of) liver, not elsewhere classified", "category": "Hepatology"},
    "nafld": {"icd10": "K76.0", "display": "Non-alcoholic fatty liver disease", "category": "Hepatology"},
    "chronic obstructive pulmonary disease": {"icd10": "J44.1", "display": "Chronic obstructive pulmonary disease with (acute) exacerbation", "category": "Pulmonology"},
    "copd": {"icd10": "J44.1", "display": "Chronic obstructive pulmonary disease with acute exacerbation", "category": "Pulmonology"},
    "community acquired pneumonia": {"icd10": "J18.9", "display": "Pneumonia, unspecified organism", "category": "Pulmonology"},
    "cap": {"icd10": "J18.9", "display": "Community-acquired pneumonia", "category": "Pulmonology"},
    "pulmonary tuberculosis": {"icd10": "A15.0", "display": "Tuberculosis of lung", "category": "Pulmonology"},
    "tuberculosis": {"icd10": "A15.0", "display": "Tuberculosis of lung", "category": "Pulmonology"},
    "tb": {"icd10": "A15.0", "display": "Tuberculosis of lung", "category": "Pulmonology"},
    "vitamin b12 deficiency": {"icd10": "E53.8", "display": "Deficiency of other specified B group vitamins", "category": "Hematology"},
    "b12 deficiency": {"icd10": "E53.8", "display": "Deficiency of other specified B group vitamins", "category": "Hematology"},
    "folate deficiency anemia": {"icd10": "D52.9", "display": "Folate deficiency anemia, unspecified", "category": "Hematology"},
    "thrombocytopenia": {"icd10": "D69.6", "display": "Thrombocytopenia, unspecified", "category": "Hematology"},
    "polycythemia vera": {"icd10": "D45", "display": "Polycythaemia vera", "category": "Hematology"},
    "ckd stage 3": {"icd10": "N18.3", "display": "Chronic kidney disease, stage 3 (moderate)", "category": "Nephrology"},
    "ckd stage 4": {"icd10": "N18.4", "display": "Chronic kidney disease, stage 4 (severe)", "category": "Nephrology"},
    "ckd stage 5": {"icd10": "N18.5", "display": "Chronic kidney disease, stage 5", "category": "Nephrology"},
    "acute kidney injury": {"icd10": "N17.9", "display": "Acute kidney failure, unspecified", "category": "Nephrology"},
    "aki": {"icd10": "N17.9", "display": "Acute kidney failure, unspecified", "category": "Nephrology"},
    "urinary tract infection": {"icd10": "N39.0", "display": "Urinary tract infection, site not specified", "category": "Urology"},
    "uti": {"icd10": "N39.0", "display": "Urinary tract infection, site not specified", "category": "Urology"},
    "benign prostatic hyperplasia": {"icd10": "N40.1", "display": "Benign prostatic hyperplasia with lower urinary tract symptoms", "category": "Urology"},
    "bph": {"icd10": "N40.1", "display": "Benign prostatic hyperplasia with LUTS", "category": "Urology"},
    "kidney stone": {"icd10": "N20.0", "display": "Calculus of kidney", "category": "Urology"},
    "nephrolithiasis": {"icd10": "N20.0", "display": "Calculus of kidney", "category": "Urology"},
    "renal calculus": {"icd10": "N20.0", "display": "Calculus of kidney", "category": "Urology"},
    "sinusitis": {"icd10": "J32.9", "display": "Chronic sinusitis, unspecified", "category": "ENT"},
    "chronic sinusitis": {"icd10": "J32.9", "display": "Chronic sinusitis, unspecified", "category": "ENT"},
    "otitis media": {"icd10": "H66.90", "display": "Otitis media, unspecified, unspecified ear", "category": "ENT"},
    "tonsillitis": {"icd10": "J03.90", "display": "Acute tonsillitis, unspecified", "category": "ENT"},
    "rheumatoid arthritis": {"icd10": "M06.9", "display": "Rheumatoid arthritis, unspecified", "category": "Rheumatology"},
    "ra": {"icd10": "M06.9", "display": "Rheumatoid arthritis, unspecified", "category": "Rheumatology"},
    "osteoarthritis": {"icd10": "M19.90", "display": "Primary osteoarthritis, unspecified site", "category": "Orthopedics"},
    "oa": {"icd10": "M19.90", "display": "Primary osteoarthritis, unspecified site", "category": "Orthopedics"},
    "gout": {"icd10": "M10.9", "display": "Gout, unspecified", "category": "Rheumatology"},
    "gouty arthritis": {"icd10": "M10.9", "display": "Gout, unspecified", "category": "Rheumatology"},
    "systemic lupus erythematosus": {"icd10": "M32.9", "display": "Systemic lupus erythematosus, unspecified", "category": "Rheumatology"},
    "sle": {"icd10": "M32.9", "display": "Systemic lupus erythematosus, unspecified", "category": "Rheumatology"},
    "osteoporosis": {"icd10": "M81.0", "display": "Age-related osteoporosis without current pathological fracture", "category": "Orthopedics"},
    "low back pain": {"icd10": "M54.50", "display": "Low back pain, unspecified", "category": "Orthopedics"},
    "lbp": {"icd10": "M54.50", "display": "Low back pain, unspecified", "category": "Orthopedics"},
    "cervical spondylosis": {"icd10": "M47.812", "display": "Spondylosis with radiculopathy, cervical region", "category": "Orthopedics"},
    "lumbar spondylosis": {"icd10": "M47.816", "display": "Spondylosis with radiculopathy, lumbar region", "category": "Orthopedics"},
    "depression": {"icd10": "F32.9", "display": "Major depressive disorder, single episode, unspecified", "category": "Psychiatry"},
    "major depressive disorder": {"icd10": "F32.9", "display": "Major depressive disorder, single episode, unspecified", "category": "Psychiatry"},
    "mdd": {"icd10": "F32.9", "display": "Major depressive disorder, single episode, unspecified", "category": "Psychiatry"},
    "anxiety disorder": {"icd10": "F41.9", "display": "Anxiety disorder, unspecified", "category": "Psychiatry"},
    "generalized anxiety disorder": {"icd10": "F41.1", "display": "Generalized anxiety disorder", "category": "Psychiatry"},
    "gad": {"icd10": "F41.1", "display": "Generalized anxiety disorder", "category": "Psychiatry"},
    "schizophrenia": {"icd10": "F20.9", "display": "Schizophrenia, unspecified", "category": "Psychiatry"},
    "bipolar disorder": {"icd10": "F31.9", "display": "Bipolar disorder, unspecified", "category": "Psychiatry"},
    "insomnia": {"icd10": "G47.00", "display": "Insomnia, unspecified", "category": "Psychiatry"},
    "glaucoma": {"icd10": "H40.9", "display": "Unspecified glaucoma", "category": "Ophthalmology"},
    "cataract": {"icd10": "H26.9", "display": "Unspecified cataract", "category": "Ophthalmology"},
    "diabetic macular edema": {"icd10": "E11.3519", "display": "Type 2 diabetes mellitus with unspecified diabetic macular edema", "category": "Ophthalmology"},
    "conjunctivitis": {"icd10": "H10.9", "display": "Unspecified conjunctivitis", "category": "Ophthalmology"},
    "psoriasis": {"icd10": "L40.9", "display": "Psoriasis, unspecified", "category": "Dermatology"},
    "eczema": {"icd10": "L30.9", "display": "Dermatitis, unspecified", "category": "Dermatology"},
    "atopic dermatitis": {"icd10": "L20.9", "display": "Atopic dermatitis, unspecified", "category": "Dermatology"},
    "urticaria": {"icd10": "L50.9", "display": "Urticaria, unspecified", "category": "Dermatology"},
    "tinea corporis": {"icd10": "B35.4", "display": "Tinea corporis", "category": "Dermatology"},
    "tinea pedis": {"icd10": "B35.3", "display": "Tinea pedis", "category": "Dermatology"},
    "acne vulgaris": {"icd10": "L70.0", "display": "Acne vulgaris", "category": "Dermatology"},
    "acne": {"icd10": "L70.0", "display": "Acne vulgaris", "category": "Dermatology"},
    "breast cancer": {"icd10": "C50.919", "display": "Malignant neoplasm of unspecified site of unspecified female breast", "category": "Oncology"},
    "lung cancer": {"icd10": "C34.10", "display": "Malignant neoplasm of upper lobe, unspecified bronchus or lung", "category": "Oncology"},
    "colorectal cancer": {"icd10": "C20", "display": "Malignant neoplasm of rectum", "category": "Oncology"},
    "prostate cancer": {"icd10": "C61", "display": "Malignant neoplasm of prostate", "category": "Oncology"},
    "cervical cancer": {"icd10": "C53.9", "display": "Malignant neoplasm of cervix uteri, unspecified", "category": "Oncology"},
    "polycystic ovarian syndrome": {"icd10": "E28.2", "display": "Polycystic ovarian syndrome", "category": "Gynecology"},
    "pcos": {"icd10": "E28.2", "display": "Polycystic ovarian syndrome", "category": "Gynecology"},
    "gestational diabetes": {"icd10": "O24.419", "display": "Gestational diabetes mellitus in pregnancy, unspecified control", "category": "Obstetrics"},
    "pregnancy induced hypertension": {"icd10": "O14.00", "display": "Mild to moderate pre-eclampsia, unspecified trimester", "category": "Obstetrics"},
    "preeclampsia": {"icd10": "O14.00", "display": "Mild to moderate pre-eclampsia, unspecified trimester", "category": "Obstetrics"},
    "dengue fever": {"icd10": "A90", "display": "Dengue fever [classical dengue]", "category": "Infectious Diseases"},
    "dengue": {"icd10": "A90", "display": "Dengue fever", "category": "Infectious Diseases"},
    "malaria": {"icd10": "B54", "display": "Unspecified malaria", "category": "Infectious Diseases"},
    "typhoid fever": {"icd10": "A01.00", "display": "Typhoid fever, unspecified", "category": "Infectious Diseases"},
    "typhoid": {"icd10": "A01.00", "display": "Typhoid fever, unspecified", "category": "Infectious Diseases"},
    "covid-19": {"icd10": "U07.1", "display": "COVID-19, virus identified", "category": "Infectious Diseases"},
    "covid 19": {"icd10": "U07.1", "display": "COVID-19, virus identified", "category": "Infectious Diseases"},
    "sepsis": {"icd10": "A41.9", "display": "Sepsis, unspecified organism", "category": "Infectious Diseases"},
    "vitamin d deficiency": {"icd10": "E55.9", "display": "Vitamin D deficiency, unspecified", "category": "Endocrinology"},
    "vit d deficiency": {"icd10": "E55.9", "display": "Vitamin D deficiency, unspecified", "category": "Endocrinology"},
}

with open(ICD10_PATH, "r", encoding="utf-8") as f:
    icd10 = json.load(f)

before = len(icd10["conditions"])
for k, v in icd10_extra.items():
    if k not in icd10["conditions"]:
        icd10["conditions"][k] = v

# Update comment
icd10["_comment"] = (
    "Authoritative ICD-10-CM diagnostic classification — v2.0. "
    "Expanded to 18 medical specialties: Endocrinology, Cardiology, Neurology, Gastroenterology, "
    "Hepatology, Pulmonology, Hematology, Nephrology, Urology, ENT, Rheumatology, Orthopedics, "
    "Psychiatry, Ophthalmology, Dermatology, Oncology, Gynecology/Obstetrics, Infectious Diseases."
)

with open(ICD10_PATH, "w", encoding="utf-8") as f:
    json.dump(icd10, f, indent=2, ensure_ascii=False)

after = len(icd10["conditions"])
print(f"ICD-10: {before} -> {after} conditions (+{after-before})")


# ── 2. Expand reference_ranges.json ──────────────────────────────────────────
REF_PATH = os.path.join(ROOT, "ai_engine", "reference_ranges.json")

extra_refs = {
    "ferritin_male": {
        "aliases": ["ferritin", "serum ferritin", "s. ferritin"],
        "loinc": "2276-4",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml", "ug/l", "mcg/l"],
        "ref_low": 12.0,
        "ref_high": 300.0,
        "sex": "M"
    },
    "ferritin_female": {
        "aliases": ["ferritin", "serum ferritin", "s. ferritin"],
        "loinc": "2276-4",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml", "ug/l", "mcg/l"],
        "ref_low": 12.0,
        "ref_high": 150.0,
        "sex": "F"
    },
    "folate": {
        "aliases": ["folate", "folic acid", "serum folate", "vitamin b9", "serum folic acid"],
        "loinc": "2132-9",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml", "nmol/l"],
        "ref_low": 3.0,
        "ref_high": 17.0
    },
    "prolactin": {
        "aliases": ["prolactin", "serum prolactin", "prl"],
        "loinc": "2842-3",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml", "miu/l"],
        "ref_low": 2.0,
        "ref_high": 18.0
    },
    "lh": {
        "aliases": ["lh", "luteinizing hormone", "lutenizing hormone", "serum lh"],
        "loinc": "10501-5",
        "unit": "mIU/mL",
        "unit_aliases": ["miu/ml", "iu/l"],
        "ref_low": 1.5,
        "ref_high": 9.3
    },
    "fsh": {
        "aliases": ["fsh", "follicle stimulating hormone", "follicle-stimulating hormone", "serum fsh"],
        "loinc": "15067-2",
        "unit": "mIU/mL",
        "unit_aliases": ["miu/ml", "iu/l"],
        "ref_low": 1.5,
        "ref_high": 12.4
    },
    "cortisol": {
        "aliases": ["cortisol", "serum cortisol", "morning cortisol", "fasting cortisol"],
        "loinc": "2143-6",
        "unit": "mcg/dL",
        "unit_aliases": ["mcg/dl", "ug/dl", "nmol/l"],
        "ref_low": 5.0,
        "ref_high": 25.0
    },
    "psa": {
        "aliases": ["psa", "prostate specific antigen", "total psa", "serum psa"],
        "loinc": "2857-1",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml"],
        "ref_low": 0.0,
        "ref_high": 4.0
    },
    "insulin_fasting": {
        "aliases": ["fasting insulin", "serum insulin", "insulin", "insulin fasting"],
        "loinc": "20448-7",
        "unit": "mcIU/mL",
        "unit_aliases": ["mciu/ml", "uiu/ml", "pmol/l"],
        "ref_low": 2.0,
        "ref_high": 25.0
    },
    "homa_ir": {
        "aliases": ["homa ir", "homa-ir", "insulin resistance index"],
        "loinc": "85354-9",
        "unit": "ratio",
        "unit_aliases": [],
        "ref_low": None,
        "ref_high": 2.5
    },
    "troponin_i": {
        "aliases": ["troponin i", "troponin", "cardiac troponin", "hs troponin i", "high sensitivity troponin i", "ctni"],
        "loinc": "89579-7",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml", "pg/ml"],
        "ref_low": None,
        "ref_high": 0.04
    },
    "troponin_t": {
        "aliases": ["troponin t", "hs troponin t", "high sensitivity troponin t", "ctnt"],
        "loinc": "67151-1",
        "unit": "ng/mL",
        "unit_aliases": ["ng/ml", "pg/ml"],
        "ref_low": None,
        "ref_high": 0.01
    },
    "d_dimer": {
        "aliases": ["d-dimer", "d dimer", "fibrin degradation product"],
        "loinc": "48066-5",
        "unit": "mg/L FEU",
        "unit_aliases": ["mg/l", "ug/ml", "ng/ml"],
        "ref_low": None,
        "ref_high": 0.5
    },
    "bnp": {
        "aliases": ["bnp", "brain natriuretic peptide", "b-type natriuretic peptide"],
        "loinc": "30934-4",
        "unit": "pg/mL",
        "unit_aliases": ["pg/ml"],
        "ref_low": None,
        "ref_high": 100.0
    },
    "nt_probnp": {
        "aliases": ["nt-probnp", "nt probnp", "n-terminal pro b-type natriuretic peptide"],
        "loinc": "33762-6",
        "unit": "pg/mL",
        "unit_aliases": ["pg/ml"],
        "ref_low": None,
        "ref_high": 125.0
    },
    "urine_microalbumin": {
        "aliases": ["microalbumin", "urine microalbumin", "microalbuminuria", "albumin urine", "spot urine albumin"],
        "loinc": "14957-5",
        "unit": "mg/L",
        "unit_aliases": ["mg/l", "mg/g"],
        "ref_low": None,
        "ref_high": 30.0
    },
    "urine_creatinine": {
        "aliases": ["urine creatinine", "spot urine creatinine", "cr urine"],
        "loinc": "2161-8",
        "unit": "mg/dL",
        "unit_aliases": ["mg/dl"],
        "ref_low": 30.0,
        "ref_high": 300.0
    },
    "magnesium": {
        "aliases": ["magnesium", "serum magnesium", "mg", "mg2+"],
        "loinc": "2593-2",
        "unit": "mg/dL",
        "unit_aliases": ["mg/dl", "mmol/l", "meq/l"],
        "ref_low": 1.7,
        "ref_high": 2.2
    },
    "phosphorus": {
        "aliases": ["phosphorus", "phosphate", "serum phosphorus", "serum phosphate", "inorganic phosphate"],
        "loinc": "2777-1",
        "unit": "mg/dL",
        "unit_aliases": ["mg/dl", "mmol/l"],
        "ref_low": 2.5,
        "ref_high": 4.5
    },
    "iron": {
        "aliases": ["iron", "serum iron", "s. iron"],
        "loinc": "2498-4",
        "unit": "mcg/dL",
        "unit_aliases": ["mcg/dl", "ug/dl", "umol/l"],
        "ref_low": 60.0,
        "ref_high": 170.0
    },
    "tibc": {
        "aliases": ["tibc", "total iron binding capacity", "serum tibc"],
        "loinc": "2501-5",
        "unit": "mcg/dL",
        "unit_aliases": ["mcg/dl", "ug/dl"],
        "ref_low": 250.0,
        "ref_high": 370.0
    },
    "transferrin_saturation": {
        "aliases": ["transferrin saturation", "tsat", "iron saturation"],
        "loinc": "2502-3",
        "unit": "%",
        "unit_aliases": ["%", "percent"],
        "ref_low": 20.0,
        "ref_high": 50.0
    },
    "ldh": {
        "aliases": ["ldh", "lactate dehydrogenase", "lactic dehydrogenase", "serum ldh"],
        "loinc": "2532-0",
        "unit": "U/L",
        "unit_aliases": ["u/l", "iu/l"],
        "ref_low": 140.0,
        "ref_high": 280.0
    },
    "ck": {
        "aliases": ["ck", "creatine kinase", "creatine phosphokinase", "cpk", "total ck"],
        "loinc": "2157-6",
        "unit": "U/L",
        "unit_aliases": ["u/l", "iu/l"],
        "ref_low": 30.0,
        "ref_high": 200.0
    },
    "ggt": {
        "aliases": ["ggt", "gamma glutamyl transferase", "gamma gt", "gamma-gt"],
        "loinc": "2324-2",
        "unit": "U/L",
        "unit_aliases": ["u/l", "iu/l"],
        "ref_low": 9.0,
        "ref_high": 48.0
    },
    "amylase": {
        "aliases": ["amylase", "serum amylase", "s. amylase"],
        "loinc": "1798-8",
        "unit": "U/L",
        "unit_aliases": ["u/l", "iu/l"],
        "ref_low": 28.0,
        "ref_high": 100.0
    },
    "lipase": {
        "aliases": ["lipase", "serum lipase"],
        "loinc": "3040-3",
        "unit": "U/L",
        "unit_aliases": ["u/l", "iu/l"],
        "ref_low": 10.0,
        "ref_high": 140.0
    },
    "bicarbonate": {
        "aliases": ["bicarbonate", "hco3", "serum bicarbonate", "total co2", "tco2"],
        "loinc": "1963-8",
        "unit": "mEq/L",
        "unit_aliases": ["meq/l", "mmol/l"],
        "ref_low": 22.0,
        "ref_high": 29.0
    },
    "inr": {
        "aliases": ["inr", "international normalized ratio", "pt inr", "prothrombin time inr"],
        "loinc": "6301-6",
        "unit": "ratio",
        "unit_aliases": [],
        "ref_low": 0.8,
        "ref_high": 1.2
    },
    "pt": {
        "aliases": ["pt", "prothrombin time", "protime", "pro time"],
        "loinc": "5902-2",
        "unit": "seconds",
        "unit_aliases": ["sec", "s"],
        "ref_low": 11.0,
        "ref_high": 13.5
    },
    "aptt": {
        "aliases": ["aptt", "activated partial thromboplastin time", "ptt", "partial thromboplastin time"],
        "loinc": "3173-2",
        "unit": "seconds",
        "unit_aliases": ["sec", "s"],
        "ref_low": 25.0,
        "ref_high": 35.0
    },
    "neutrophils": {
        "aliases": ["neutrophils", "neutrophil count", "polymorphonuclear", "pmn", "seg", "segmented neutrophils"],
        "loinc": "26499-4",
        "unit": "%",
        "unit_aliases": ["%", "percent"],
        "ref_low": 40.0,
        "ref_high": 80.0
    },
    "lymphocytes": {
        "aliases": ["lymphocytes", "lymphocyte count", "lymph count"],
        "loinc": "26474-7",
        "unit": "%",
        "unit_aliases": ["%", "percent"],
        "ref_low": 20.0,
        "ref_high": 40.0
    },
    "eosinophils": {
        "aliases": ["eosinophils", "eosinophil count", "eos"],
        "loinc": "26449-9",
        "unit": "%",
        "unit_aliases": ["%", "percent"],
        "ref_low": 1.0,
        "ref_high": 6.0
    },
    "monocytes": {
        "aliases": ["monocytes", "monocyte count", "mono"],
        "loinc": "26484-6",
        "unit": "%",
        "unit_aliases": ["%", "percent"],
        "ref_low": 2.0,
        "ref_high": 10.0
    },
    "mcv": {
        "aliases": ["mcv", "mean corpuscular volume", "mean cell volume"],
        "loinc": "787-2",
        "unit": "fL",
        "unit_aliases": ["fl"],
        "ref_low": 80.0,
        "ref_high": 100.0
    },
    "mch": {
        "aliases": ["mch", "mean corpuscular hemoglobin", "mean cell hemoglobin"],
        "loinc": "785-6",
        "unit": "pg",
        "unit_aliases": ["pg"],
        "ref_low": 27.0,
        "ref_high": 33.0
    },
    "mchc": {
        "aliases": ["mchc", "mean corpuscular hemoglobin concentration"],
        "loinc": "786-4",
        "unit": "g/dL",
        "unit_aliases": ["g/dl"],
        "ref_low": 31.5,
        "ref_high": 36.0
    },
    "rdw": {
        "aliases": ["rdw", "red cell distribution width", "rdw-cv"],
        "loinc": "788-0",
        "unit": "%",
        "unit_aliases": ["%"],
        "ref_low": 11.5,
        "ref_high": 14.5
    },
    "hba1c_diabetic_control": {
        "aliases": ["hba1c target", "hba1c goal"],
        "loinc": "4548-4",
        "unit": "%",
        "unit_aliases": ["%"],
        "ref_low": None,
        "ref_high": 7.0
    },
    "microalbuminuria_ratio": {
        "aliases": ["acr", "albumin creatinine ratio", "urine acr", "albumin to creatinine ratio"],
        "loinc": "14959-1",
        "unit": "mg/g",
        "unit_aliases": ["mg/g"],
        "ref_low": None,
        "ref_high": 30.0
    },
    "random_insulin": {
        "aliases": ["random insulin", "post prandial insulin", "insulin pp"],
        "loinc": "20448-7",
        "unit": "mcIU/mL",
        "unit_aliases": ["mciu/ml", "uiu/ml"],
        "ref_low": None,
        "ref_high": 60.0
    },
    "ige_total": {
        "aliases": ["total ige", "ige", "serum ige", "immunoglobulin e"],
        "loinc": "19113-0",
        "unit": "IU/mL",
        "unit_aliases": ["iu/ml", "ku/l"],
        "ref_low": None,
        "ref_high": 100.0
    },
    "anti_tpo": {
        "aliases": ["anti tpo", "anti-tpo", "anti thyroid peroxidase", "tpo antibody", "thyroid peroxidase antibody"],
        "loinc": "56740-1",
        "unit": "IU/mL",
        "unit_aliases": ["iu/ml"],
        "ref_low": None,
        "ref_high": 35.0
    },
    "anti_tg": {
        "aliases": ["anti tg", "anti-tg", "anti thyroglobulin", "thyroglobulin antibody", "tg antibody"],
        "loinc": "56741-9",
        "unit": "IU/mL",
        "unit_aliases": ["iu/ml"],
        "ref_low": None,
        "ref_high": 40.0
    },
    "hiv": {
        "aliases": ["hiv", "hiv 1/2", "hiv antigen antibody", "hiv combo test"],
        "loinc": "75622-1",
        "unit": "reactive/non-reactive",
        "unit_aliases": [],
        "ref_low": None,
        "ref_high": None
    },
    "hbsag": {
        "aliases": ["hbsag", "hepatitis b surface antigen", "hbs antigen", "hepatitis b s antigen"],
        "loinc": "5195-3",
        "unit": "reactive/non-reactive",
        "unit_aliases": [],
        "ref_low": None,
        "ref_high": None
    },
    "anti_hcv": {
        "aliases": ["anti hcv", "hepatitis c antibody", "hcv antibody", "anti hepatitis c"],
        "loinc": "16128-1",
        "unit": "reactive/non-reactive",
        "unit_aliases": [],
        "ref_low": None,
        "ref_high": None
    },
    "dengue_ns1": {
        "aliases": ["dengue ns1", "ns1 antigen", "dengue ns1 antigen", "dengue antigen"],
        "loinc": "41461-5",
        "unit": "reactive/non-reactive",
        "unit_aliases": [],
        "ref_low": None,
        "ref_high": None
    },
    "malaria_rdt": {
        "aliases": ["malaria rdt", "malaria antigen", "rapid malaria test", "malaria rapid test"],
        "loinc": "32700-7",
        "unit": "reactive/non-reactive",
        "unit_aliases": [],
        "ref_low": None,
        "ref_high": None
    }
}

with open(REF_PATH, "r", encoding="utf-8-sig") as f:
    ref = json.load(f)

before_r = len(ref["tests"])
for k, v in extra_refs.items():
    if k not in ref["tests"]:
        ref["tests"][k] = v

ref["_comment"] = (
    "Authoritative Reference Ranges — v2.0 based on LOINC and Standard Clinical Pathology Laboratory "
    "Guidelines (WHO, IFCC, NABL). Expanded with ferritin, folate, hormones, cardiac biomarkers, "
    "coagulation, CBC differentials, iron studies, immunology, infectious disease serology, and more."
)

with open(REF_PATH, "w", encoding="utf-8") as f:
    json.dump(ref, f, indent=2, ensure_ascii=False)

after_r = len(ref["tests"])
print(f"Reference ranges: {before_r} -> {after_r} tests (+{after_r-before_r})")


# ── 3. Expand aliases.json ────────────────────────────────────────────────────
ALIAS_PATH = os.path.join(ROOT, "ai_engine", "aliases.json")

extra_aliases = {
    "ferritin": "Ferritin",
    "serum ferritin": "Ferritin",
    "s. ferritin": "Ferritin",
    "folic acid": "Folate",
    "folate": "Folate",
    "vitamin b9": "Folate",
    "prolactin": "Prolactin",
    "prl": "Prolactin",
    "luteinizing hormone": "LH",
    "lutenizing hormone": "LH",
    "follicle stimulating hormone": "FSH",
    "follicle-stimulating hormone": "FSH",
    "cortisol": "Cortisol",
    "morning cortisol": "Cortisol",
    "prostate specific antigen": "PSA",
    "total psa": "PSA",
    "fasting insulin": "Fasting Insulin",
    "serum insulin": "Fasting Insulin",
    "troponin": "Troponin I",
    "troponin i": "Troponin I",
    "cardiac troponin": "Troponin I",
    "ctni": "Troponin I",
    "troponin t": "Troponin T",
    "ctnt": "Troponin T",
    "d-dimer": "D-Dimer",
    "d dimer": "D-Dimer",
    "bnp": "BNP",
    "brain natriuretic peptide": "BNP",
    "nt-probnp": "NT-proBNP",
    "nt probnp": "NT-proBNP",
    "microalbumin": "Microalbumin",
    "microalbuminuria": "Microalbumin",
    "urine microalbumin": "Microalbumin",
    "magnesium": "Magnesium",
    "serum magnesium": "Magnesium",
    "phosphate": "Phosphorus",
    "phosphorus": "Phosphorus",
    "serum phosphate": "Phosphorus",
    "serum iron": "Iron",
    "s. iron": "Iron",
    "tibc": "TIBC",
    "total iron binding capacity": "TIBC",
    "tsat": "Transferrin Saturation",
    "transferrin saturation": "Transferrin Saturation",
    "iron saturation": "Transferrin Saturation",
    "ldh": "LDH",
    "lactate dehydrogenase": "LDH",
    "lactic dehydrogenase": "LDH",
    "ck": "CK",
    "creatine kinase": "CK",
    "cpk": "CK",
    "creatine phosphokinase": "CK",
    "ggt": "GGT",
    "gamma glutamyl transferase": "GGT",
    "gamma-gt": "GGT",
    "amylase": "Amylase",
    "serum amylase": "Amylase",
    "lipase": "Lipase",
    "serum lipase": "Lipase",
    "inr": "INR",
    "international normalized ratio": "INR",
    "pt inr": "INR",
    "prothrombin time inr": "INR",
    "prothrombin time": "PT",
    "protime": "PT",
    "aptt": "APTT",
    "activated partial thromboplastin time": "APTT",
    "ptt": "APTT",
    "neutrophils": "Neutrophils",
    "polymorphonuclear": "Neutrophils",
    "pmn": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "lymph count": "Lymphocytes",
    "eosinophils": "Eosinophils",
    "monocytes": "Monocytes",
    "mcv": "MCV",
    "mean corpuscular volume": "MCV",
    "mean cell volume": "MCV",
    "mch": "MCH",
    "mean corpuscular hemoglobin": "MCH",
    "mchc": "MCHC",
    "rdw": "RDW",
    "red cell distribution width": "RDW",
    "acr": "ACR",
    "albumin creatinine ratio": "ACR",
    "urine acr": "ACR",
    "total ige": "Total IgE",
    "ige": "Total IgE",
    "immunoglobulin e": "Total IgE",
    "anti tpo": "Anti-TPO",
    "anti-tpo": "Anti-TPO",
    "tpo antibody": "Anti-TPO",
    "thyroid peroxidase antibody": "Anti-TPO",
    "anti tg": "Anti-Tg",
    "anti-tg": "Anti-Tg",
    "thyroglobulin antibody": "Anti-Tg",
    "hbsag": "HBsAg",
    "hepatitis b surface antigen": "HBsAg",
    "anti hcv": "Anti-HCV",
    "hepatitis c antibody": "Anti-HCV",
    "hcv antibody": "Anti-HCV",
    "dengue ns1": "Dengue NS1",
    "ns1 antigen": "Dengue NS1",
    "dengue ns1 antigen": "Dengue NS1",
    "hiv": "HIV",
    "hiv 1/2": "HIV",
    "hiv combo test": "HIV",
    "widal": "Widal Test",
    "mp smear": "Malaria Smear",
    "peripheral smear": "Peripheral Smear",
    "abo blood group": "Blood Group",
    "blood group typing": "Blood Group",
    "blood grouping": "Blood Group",
}

with open(ALIAS_PATH, "r", encoding="utf-8") as f:
    aliases = json.load(f)

before_a = len(aliases["aliases"])
for k, v in extra_aliases.items():
    if k not in aliases["aliases"]:
        aliases["aliases"][k] = v

aliases["_comment"] = "Canonical test alias mapping table v2.0 — Indian and International laboratory reports. Expanded with hormones, cardiac biomarkers, iron studies, serology, coagulation, CBC differentials."

with open(ALIAS_PATH, "w", encoding="utf-8") as f:
    json.dump(aliases, f, indent=2, ensure_ascii=False)

after_a = len(aliases["aliases"])
print(f"Aliases: {before_a} -> {after_a} entries (+{after_a-before_a})")


# ── 4. Expand brands.csv ──────────────────────────────────────────────────────
BRANDS_PATH = os.path.join(ROOT, "ai_engine", "brands.csv")

extra_brands = [
    # Neurology
    ["Lobazam 10", "Clobazam", "10 mg"],
    ["Lobazam 5", "Clobazam", "5 mg"],
    ["Oxetol 150", "Oxcarbazepine", "150 mg"],
    ["Oxetol 300", "Oxcarbazepine", "300 mg"],
    ["Oxetol 600", "Oxcarbazepine", "600 mg"],
    ["Valparin 200", "Sodium Valproate", "200 mg"],
    ["Valparin CR 300", "Sodium Valproate (CR)", "300 mg"],
    ["Valparin CR 500", "Sodium Valproate (CR)", "500 mg"],
    ["Eptoin 50", "Phenytoin", "50 mg"],
    ["Eptoin 100", "Phenytoin", "100 mg"],
    ["Tegretol 200", "Carbamazepine", "200 mg"],
    ["Tegretol 400", "Carbamazepine", "400 mg"],
    ["Lamictal 25", "Lamotrigine", "25 mg"],
    ["Lamictal 50", "Lamotrigine", "50 mg"],
    ["Paxidep CR 12.5", "Paroxetine CR", "12.5 mg"],
    ["Paxidep CR 25", "Paroxetine CR", "25 mg"],
    ["Risdone 1", "Risperidone", "1 mg"],
    ["Risdone 2", "Risperidone", "2 mg"],
    ["Oleanz 2.5", "Olanzapine", "2.5 mg"],
    ["Oleanz 5", "Olanzapine", "5 mg"],
    ["Oleanz 10", "Olanzapine", "10 mg"],
    ["Qutan 25", "Quetiapine", "25 mg"],
    ["Qutan 50", "Quetiapine", "50 mg"],
    ["Qutan 100", "Quetiapine", "100 mg"],
    ["Syndopa 275", "Levodopa + Carbidopa", "250 mg + 25 mg"],
    ["Syndopa CR 250", "Levodopa + Carbidopa (CR)", "200 mg + 50 mg"],
    ["Pramipex 0.25", "Pramipexole", "0.25 mg"],
    ["Pramipex 1", "Pramipexole", "1 mg"],
    # Cardiology
    ["Warfin 1", "Warfarin", "1 mg"],
    ["Warfin 2", "Warfarin", "2 mg"],
    ["Warfin 5", "Warfarin", "5 mg"],
    ["Xarelto 15", "Rivaroxaban", "15 mg"],
    ["Xarelto 20", "Rivaroxaban", "20 mg"],
    ["Eliquis 2.5", "Apixaban", "2.5 mg"],
    ["Eliquis 5", "Apixaban", "5 mg"],
    ["Praluent 75", "Alirocumab", "75 mg/mL"],
    ["Sotret 10", "Isotretinoin", "10 mg"],
    ["Sotret 20", "Isotretinoin", "20 mg"],
    ["Labetalol 100", "Labetalol", "100 mg"],
    ["Labetalol 200", "Labetalol", "200 mg"],
    ["Minipress 1", "Prazosin", "1 mg"],
    ["Minipress 2", "Prazosin", "2 mg"],
    ["Aldactone 25", "Spironolactone", "25 mg"],
    ["Aldactone 50", "Spironolactone", "50 mg"],
    ["Lasix 40", "Furosemide", "40 mg"],
    ["Lasix 80", "Furosemide", "80 mg"],
    ["Dytor 5", "Torasemide", "5 mg"],
    ["Dytor 10", "Torasemide", "10 mg"],
    # Gastroenterology
    ["Colimex 10", "Dicyclomine", "10 mg"],
    ["Buscopan 10", "Hyoscine Butylbromide", "10 mg"],
    ["Lomotil", "Diphenoxylate + Atropine", "2.5 mg + 0.025 mg"],
    ["Cremaffin", "Liquid Paraffin + Milk of Magnesia", ""],
    ["Isabgol", "Psyllium Husk", ""],
    ["Macpee PD", "Macrogol 4000", ""],
    ["Lactulose", "Lactulose", "10 g/15 mL"],
    ["Rifagut 400", "Rifaximin", "400 mg"],
    ["Rifaximin 550", "Rifaximin", "550 mg"],
    ["Ursocol 150", "Ursodeoxycholic Acid", "150 mg"],
    ["Ursocol 300", "Ursodeoxycholic Acid", "300 mg"],
    # Nephrology / Urology
    ["Calutide 50", "Bicalutamide", "50 mg"],
    ["Dutahair 0.5", "Dutasteride", "0.5 mg"],
    ["Avodart 0.5", "Dutasteride", "0.5 mg"],
    ["Flomax 0.4", "Tamsulosin", "0.4 mg"],
    ["Urimax 0.4", "Tamsulosin", "0.4 mg"],
    ["Silodal 8", "Silodosin", "8 mg"],
    ["Veltam 0.4", "Tamsulosin", "0.4 mg"],
    ["Cystone", "Herbal Urinary Supplement", ""],
    ["Neeri", "Herbal Urinary Supplement", ""],
    # Pulmonology
    ["Seroflo 250", "Salmeterol + Fluticasone", "50 mcg + 250 mcg"],
    ["Seroflo 500", "Salmeterol + Fluticasone", "50 mcg + 500 mcg"],
    ["Foracort 400", "Formoterol + Budesonide", "6 mcg + 400 mcg"],
    ["Spiriva 18", "Tiotropium", "18 mcg"],
    ["Duolin Inhaler", "Levosalbutamol + Ipratropium", "50 mcg + 20 mcg"],
    ["Atrovent", "Ipratropium", "20 mcg"],
    ["Roflucor 0.5", "Roflumilast", "0.5 mg"],
    ["Aerocort Inhaler", "Beclomethasone + Levosalbutamol", "100 mcg + 50 mcg"],
    ["Asthalin Rotacaps", "Salbutamol", "200 mcg"],
    ["Cofsils", "Amylmetacresol + Dichlorobenzyl", ""],
    # Endocrinology/Diabetes
    ["Ozempic 0.25", "Semaglutide", "0.25 mg"],
    ["Ozempic 0.5", "Semaglutide", "0.5 mg"],
    ["Ozempic 1", "Semaglutide", "1 mg"],
    ["Victoza 1.2", "Liraglutide", "1.2 mg"],
    ["Victoza 1.8", "Liraglutide", "1.8 mg"],
    ["Galvus 50", "Vildagliptin", "50 mg"],
    ["Galvus Met 50/500", "Vildagliptin + Metformin", "50 mg + 500 mg"],
    ["Invokana 100", "Canagliflozin", "100 mg"],
    ["Invokana 300", "Canagliflozin", "300 mg"],
    ["Synjardy 10/500", "Empagliflozin + Metformin", "10 mg + 500 mg"],
    ["Dapagliflozin 10", "Dapagliflozin", "10 mg"],
    ["Actos 15", "Pioglitazone", "15 mg"],
    ["Actos 30", "Pioglitazone", "30 mg"],
    ["Pioglit 15", "Pioglitazone", "15 mg"],
    ["Glimestar M1", "Glimepiride + Metformin", "1 mg + 500 mg"],
    ["Glimestar M2", "Glimepiride + Metformin", "2 mg + 500 mg"],
    ["Amaryl 1", "Glimepiride", "1 mg"],
    ["Amaryl 2", "Glimepiride", "2 mg"],
    ["Amaryl 3", "Glimepiride", "3 mg"],
    ["Okamet 500", "Metformin", "500 mg"],
    ["Okamet 850", "Metformin", "850 mg"],
    ["Bigomet SR 500", "Metformin (SR)", "500 mg"],
    ["Biosulin N", "Isophane Insulin", "100 IU/mL"],
    ["Biosulin R", "Regular Insulin", "100 IU/mL"],
    ["Lantus 100", "Insulin Glargine", "100 units/mL"],
    ["Basalin 100", "Insulin Glargine", "100 units/mL"],
    ["Novorapid", "Insulin Aspart", "100 units/mL"],
    ["Humalog", "Insulin Lispro", "100 units/mL"],
    ["Huminsulin 30/70", "Isophane + Neutral Insulin", "30/70 IU/mL"],
    # Rheumatology / Orthopedics
    ["Hcqs 200", "Hydroxychloroquine", "200 mg"],
    ["Hcqs 400", "Hydroxychloroquine", "400 mg"],
    ["Wysolone 5", "Prednisolone", "5 mg"],
    ["Wysolone 10", "Prednisolone", "10 mg"],
    ["Wysolone 20", "Prednisolone", "20 mg"],
    ["Medrol 4", "Methylprednisolone", "4 mg"],
    ["Medrol 8", "Methylprednisolone", "8 mg"],
    ["Medrol 16", "Methylprednisolone", "16 mg"],
    ["Folitrax 7.5", "Methotrexate", "7.5 mg"],
    ["Folitrax 10", "Methotrexate", "10 mg"],
    ["Sulfamethox", "Sulfasalazine", "500 mg"],
    ["Salazopyrin 500", "Sulfasalazine", "500 mg"],
    ["Calcimax 500", "Calcium Carbonate + Vitamin D3", "500 mg + 400 IU"],
    ["Ostocalcium D3", "Calcium Carbonate + Vitamin D3", "500 mg + 400 IU"],
    ["Zolefit 5mg", "Zoledronic Acid", "5 mg"],
    ["Axodin 35", "Alendronate", "35 mg"],
    ["Axodin 70", "Alendronate", "70 mg"],
    ["Alendrate 70", "Alendronate", "70 mg"],
    ["Nucoxia 60", "Etoricoxib", "60 mg"],
    ["Nucoxia 90", "Etoricoxib", "90 mg"],
    ["Nucoxia 120", "Etoricoxib", "120 mg"],
    ["Arcoxia 60", "Etoricoxib", "60 mg"],
    ["Arcoxia 90", "Etoricoxib", "90 mg"],
    ["Zerodol P", "Aceclofenac + Paracetamol", "100 mg + 500 mg"],
    ["Zerodol SP", "Aceclofenac + Paracetamol + Serratiopeptidase", "100 mg + 325 mg + 10 mg"],
    ["Nicip 100", "Nimesulide", "100 mg"],
    ["Nise 100", "Nimesulide", "100 mg"],
    ["Diclofenac 50", "Diclofenac Sodium", "50 mg"],
    # Psychiatry
    ["Citalopram 20", "Citalopram", "20 mg"],
    ["Fluoxetine 20", "Fluoxetine", "20 mg"],
    ["Fludac 20", "Fluoxetine", "20 mg"],
    ["Sertraline 50", "Sertraline", "50 mg"],
    ["Serta 50", "Sertraline", "50 mg"],
    ["Venlafaxine XR 37.5", "Venlafaxine XR", "37.5 mg"],
    ["Venlafaxine XR 75", "Venlafaxine XR", "75 mg"],
    ["Veniz XR 37.5", "Venlafaxine XR", "37.5 mg"],
    ["Mirtaz 7.5", "Mirtazapine", "7.5 mg"],
    ["Mirtaz 15", "Mirtazapine", "15 mg"],
    ["Clonazepam 0.25", "Clonazepam", "0.25 mg"],
    ["Clonazepam 0.5", "Clonazepam", "0.5 mg"],
    ["Clonazepam 1", "Clonazepam", "1 mg"],
    ["Clonotril 0.25", "Clonazepam", "0.25 mg"],
    ["Clonotril 0.5", "Clonazepam", "0.5 mg"],
    ["Nitrazepam 5", "Nitrazepam", "5 mg"],
    ["Alprax 0.25", "Alprazolam", "0.25 mg"],
    ["Alprax 0.5", "Alprazolam", "0.5 mg"],
    ["Restyl 0.25", "Alprazolam", "0.25 mg"],
    # Dermatology
    ["Betnovate N", "Betamethasone + Neomycin", "0.1% + 0.5%"],
    ["Dermovate", "Clobetasol Propionate", "0.05%"],
    ["Candid B", "Clotrimazole + Beclomethasone", "1% + 0.025%"],
    ["Candid Cream", "Clotrimazole", "1%"],
    ["Fluconazole 150", "Fluconazole", "150 mg"],
    ["Forcan 150", "Fluconazole", "150 mg"],
    ["Terbinafine 250", "Terbinafine", "250 mg"],
    ["Lamisil 250", "Terbinafine", "250 mg"],
    ["Mometasone Cream", "Mometasone Furoate", "0.1%"],
    ["Elocon Cream", "Mometasone Furoate", "0.1%"],
    ["Acutret 20", "Isotretinoin", "20 mg"],
    ["Isotret 10", "Isotretinoin", "10 mg"],
    ["Clindac A Gel", "Clindamycin", "1%"],
    ["Doxycycline 100", "Doxycycline", "100 mg"],
    ["Doxt 100", "Doxycycline", "100 mg"],
    ["Minoz 50", "Minocycline", "50 mg"],
    ["Minoz 100", "Minocycline", "100 mg"],
    # Ophthalmology
    ["Genteal Eye Drops", "Hypromellose", "0.3%"],
    ["Systane Ultra", "Polyethylene Glycol + Propylene Glycol", "0.4% + 0.3%"],
    ["Timolol 0.5%", "Timolol Maleate", "0.5%"],
    ["Xalatan 0.005%", "Latanoprost", "0.005%"],
    ["Combigan", "Brimonidine + Timolol", "0.2% + 0.5%"],
    ["Tobramycin Eye Drops", "Tobramycin", "0.3%"],
    ["Moxifloxacin Eye Drops", "Moxifloxacin", "0.5%"],
    ["Pred Forte", "Prednisolone Acetate", "1%"],
    # Antibiotics (extended)
    ["Levofloxacin 500", "Levofloxacin", "500 mg"],
    ["Levobact 500", "Levofloxacin", "500 mg"],
    ["Taxim 1g", "Ceftriaxone", "1000 mg"],
    ["Ceftas 200", "Cefixime", "200 mg"],
    ["Amoxy 250", "Amoxicillin", "250 mg"],
    ["Metronidazole 400", "Metronidazole", "400 mg"],
    ["Flagyl 400", "Metronidazole", "400 mg"],
    ["Tiniba 500", "Tinidazole", "500 mg"],
    ["Clindamycin 300", "Clindamycin", "300 mg"],
    ["Vancomycin 500", "Vancomycin", "500 mg"],
    ["Amikacin 250", "Amikacin", "250 mg"],
    ["Meropenem 500", "Meropenem", "500 mg"],
    ["Meropenem 1g", "Meropenem", "1000 mg"],
    ["Pip Tazo 4.5g", "Piperacillin + Tazobactam", "4000 mg + 500 mg"],
    ["Rifampicin 450", "Rifampicin", "450 mg"],
    ["Rifampicin 600", "Rifampicin", "600 mg"],
    ["Isoniazid 300", "Isoniazid", "300 mg"],
    ["Pyrazinamide 500", "Pyrazinamide", "500 mg"],
    ["Ethambutol 400", "Ethambutol", "400 mg"],
    ["Akurit 4", "Rifampicin + Isoniazid + Pyrazinamide + Ethambutol", "450+300+750+800 mg"],
    # Supplements (extended)
    ["Zinco 22", "Zinc Sulphate", "22 mg"],
    ["Zincovit", "Zinc + Vitamins", ""],
    ["Evion 400", "Vitamin E", "400 mg"],
    ["Evion 600", "Vitamin E", "600 mg"],
    ["Mecobalamin 500", "Methylcobalamin", "500 mcg"],
    ["Nervijen P", "Methylcobalamin + Pregabalin", "500 mcg + 75 mg"],
    ["Pregabalin 150", "Pregabalin", "150 mg"],
    ["Gabapin 300", "Gabapentin", "300 mg"],
    ["Gabapin NT 100", "Gabapentin + Nortriptyline", "300 mg + 10 mg"],
    ["Capsaicin Cream", "Capsaicin", "0.025%"],
]

with open(BRANDS_PATH, "r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = rows[0]
existing_brands = {r[0].lower() for r in rows[1:] if r}
new_rows = []
for b in extra_brands:
    if b[0].lower() not in existing_brands:
        new_rows.append(b)
        existing_brands.add(b[0].lower())

with open(BRANDS_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)
    writer.writerows(new_rows)

print(f"Brands: {len(rows)-1} -> {len(rows)-1+len(new_rows)} entries (+{len(new_rows)})")

print("\nAll data expansion complete!")
