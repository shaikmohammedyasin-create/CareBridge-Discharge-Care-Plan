# Generator for 2,000 synthetic discharge summaries with ground truth
# Implements Step 6 dataset generation
# Co-Authored-By: Claude Code <noreply@anthropic.com>

import json
import random
from pathlib import Path

# Deterministic seed for reproducible evaluation dataset
random.seed(42)

FIRST_NAMES = [
    "Ramesh", "Suresh", "Mahesh", "Rajesh", "Venkatesh", "Krishna", "Ramana",
    "Subba", "Appa", "Srinivasa", "Narayana", "Mohan", "Prasad", "Satish",
    "Lakshmi", "Sita", "Parvathi", "Padmavathi", "Kavitha", "Anasuya", "Saraswathi",
    "Radha", "Bhanumathi", "Hemalatha", "Geetha", "Sujatha", "Swapna", "Sirisha"
]
LAST_NAMES = ["Kumar", "Rao", "Reddy", "Murthy", "Naidu", "Sharma", "Varma", "Devi", "Bai", "Amma"]

CONDITIONS = {
    "diabetes": {
        "drugs": [
            ("Tab Metformin", "500 mg", "BD", "pc", "30 days", "Metformin"),
            ("Tab Metformin", "1000 mg", "BD", "pc", "60 days", "Metformin"),
            ("Tab Glimepiride", "1 mg", "OD", "ac", "30 days", "Glimepiride"),
            ("Tab Glimepiride", "2 mg", "OD", "ac", "30 days", "Glimepiride"),
            ("Tab Januvia", "100 mg", "OD", "pc", "30 days", "Sitagliptin"),
            ("Tab Forxiga", "10 mg", "OD", "pc", "30 days", "Dapagliflozin"),
            ("Tab Galvus", "50 mg", "BD", "pc", "30 days", "Vildagliptin"),
        ],
        "warnings": ["severe dizziness", "sweating", "confusion", "blurred vision"],
        "diet": ["diabetic diet", "avoid sweets", "low carbohydrate diet"],
        "activity": ["regular walking 20 mins daily", "brisk walking", "light morning walk"],
        "depts": ["Endocrine OPD", "Diabetic Clinic", "General Medicine OPD"]
    },
    "cardiac": {
        "drugs": [
            ("Tab Amlodipine", "5 mg", "OD", "pc", "30 days", "Amlodipine"),
            ("Tab Telmisartan", "40 mg", "OD", "pc", "30 days", "Telmisartan"),
            ("Tab Atorvastatin", "20 mg", "HS", "at bedtime", "30 days", "Atorvastatin"),
            ("Tab Aspirin", "75 mg", "OD", "pc", "90 days", "Aspirin"),
            ("Tab Clopidogrel", "75 mg", "OD", "pc", "90 days", "Clopidogrel"),
            ("Tab Lasix", "20 mg", "OD", "pc", "15 days", "Furosemide"),
            ("Tab Tenormin", "50 mg", "OD", "pc", "30 days", "Atenolol"),
        ],
        "warnings": ["chest pain", "shortness of breath", "cold sweats", "swelling in feet"],
        "diet": ["low salt diet", "low fat diet", "avoid salted pickles"],
        "activity": ["avoid heavy lifting", "gentle walking", "adequate bed rest"],
        "depts": ["Cardiology OPD", "Cardiac Review Clinic", "General Medicine"]
    },
    "respiratory": {
        "drugs": [
            ("Inhaler Salbutamol", "100 mcg", "SOS", "when needed", "30 days", "Salbutamol"),
            ("Inhaler Budecort", "200 mcg", "BD", "inhalation", "30 days", "Budesonide"),
            ("Tab Montelukast", "10 mg", "HS", "at bedtime", "30 days", "Montelukast"),
            ("Tab Deriphyllin", "150 mg", "BD", "pc", "14 days", "Theophylline and Etophylline"),
            ("Tab Azithral", "500 mg", "OD", "pc", "3 days", "Azithromycin"),
        ],
        "warnings": ["severe breathlessness", "chest tightness", "wheezing", "high fever"],
        "diet": ["warm fluids", "adequate hydration", "avoid cold foods and drinks"],
        "activity": ["breathing exercises", "avoid dust exposure", "rest at home"],
        "depts": ["Pulmonology OPD", "Chest Clinic", "Respiratory Care OPD"]
    },
    "post_op": {
        "drugs": [
            ("Tab Augmentin", "625 mg", "BD", "pc", "5 days", "Amoxicillin and Potassium Clavulanate"),
            ("Tab Paracetamol", "650 mg", "TDS", "pc", "3 days", "Paracetamol"),
            ("Tab Pantoprazole", "40 mg", "OD", "ac", "7 days", "Pantoprazole"),
            ("Tab Voveran", "50 mg", "BD", "pc", "5 days", "Diclofenac"),
            ("Tab Ultracet", "325 mg", "TDS", "pc", "3 days", "Tramadol and Paracetamol"),
            ("Tab Zifi", "200 mg", "BD", "pc", "5 days", "Cefixime"),
        ],
        "warnings": ["wound redness", "high fever", "pus discharge", "excessive bleeding"],
        "diet": ["high protein diet", "soft easily digestible diet", "plenty of clean water"],
        "activity": ["avoid heavy lifting for 4 weeks", "strict bed rest for 3 days", "no strenuous work"],
        "depts": ["Surgical OPD", "Post-Op Clinic", "Surgery Review OPD"]
    },
    "maternity": {
        "drugs": [
            ("Tab Folvite", "5 mg", "OD", "pc", "30 days", "Folic Acid"),
            ("Tab Shelcal", "500 mg", "BD", "pc", "30 days", "Calcium and Vitamin D3"),
            ("Tab Orofer-XT", "100 mg", "OD", "pc", "30 days", "Ferrous Ascorbate and Folic Acid"),
            ("Tab Labetalol", "100 mg", "BD", "pc", "14 days", "Labetalol"),
            ("Tab Gestofit", "200 mg", "HS", "at bedtime", "14 days", "Progesterone"),
        ],
        "warnings": ["heavy vaginal bleeding", "severe lower abdominal pain", "severe headache", "blurred vision"],
        "diet": ["high iron diet", "adequate hydration", "green leafy vegetables and milk"],
        "activity": ["avoid heavy household chores", "adequate rest", "gentle mobilization"],
        "depts": ["Maternity OPD", "Obstetrics Clinic", "Postnatal Review OPD"]
    }
}


def generate_dataset():
    items = []
    groups = list(CONDITIONS.keys())

    for idx in range(1, 2001):
        group_name = groups[(idx - 1) % len(groups)]
        g_data = CONDITIONS[group_name]

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        age = random.randint(20, 78) if group_name != "maternity" else random.randint(20, 38)

        # Select 1 to 3 distinct drugs
        num_drugs = random.randint(1, 3)
        chosen_drugs = random.sample(g_data["drugs"], min(num_drugs, len(g_data["drugs"])))

        # Ambiguity injection for ~8% of cases to test safe failure and honest abstain calibration
        is_ambiguous = (idx % 12 == 0)
        if is_ambiguous:
            # Add an ambiguous short form or eye drop OD
            chosen_drugs = list(chosen_drugs)
            chosen_drugs.append(("Eye Drops Ciprofloxacin", "0.3%", "OD", "topical", "7 days", "Ciprofloxacin"))

        # Follow up date: between 24/10/2026 and 30/11/2026
        day = random.randint(1, 28)
        month = random.choice([10, 11])
        fu_date = f"{day:02d}/{month:02d}/2026"
        iso_date = f"2026-{month:02d}-{day:02d}"
        dept = random.choice(g_data["depts"])

        warnings = random.sample(g_data["warnings"], random.randint(1, 2))
        diet = random.sample(g_data["diet"], random.randint(1, 2))
        activity = random.sample(g_data["activity"], 1)

        # Build discharge summary text
        lines = [
            "DISCHARGE SUMMARY",
            f"Patient Name: {name} Age: {age}",
            f"Condition: {group_name.replace('_', ' ').title()}",
            "Medications:"
        ]
        expected_meds = []
        for d in chosen_drugs:
            mname, mdose, mfreq, mtime, mdur, mgen = d
            lines.append(f"{mname} {mdose} {mfreq} {mtime} x {mdur}")
            expected_meds.append({
                "generic": mgen,
                "dose": mdose,
                "freq": mfreq,
                "dur": mdur
            })

        lines.append(f"Follow-up: Review in {dept} on {fu_date}")
        lines.append(f"Warning signs: {', '.join(warnings)}")
        lines.append(f"Diet: {', '.join(diet)}")
        lines.append(f"Activity: {', '.join(activity)}")

        summary_text = "\n".join(lines)

        items.append({
            "id": idx,
            "patient_name": name,
            "patient_age": age,
            "category": group_name,
            "summary": summary_text,
            "expected_medicines": expected_meds,
            "expected_follow_up": iso_date,
            "is_ambiguous": is_ambiguous
        })

    out_file = Path("data/samples/synthetic_2000.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    print(f"Successfully generated {len(items)} synthetic discharge summaries in {out_file}")


if __name__ == "__main__":
    generate_dataset()
