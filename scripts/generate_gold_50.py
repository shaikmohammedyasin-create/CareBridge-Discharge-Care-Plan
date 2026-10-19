# Generator for 50 diverse clinical gold summaries
# Co-Authored-By: Claude Code <noreply@anthropic.com>

import json
from pathlib import Path

cases = [
    # 1-10 Diabetes
    ("Ramesh Kumar", 52, "diabetes", [("Tab Metformin", "500 mg", "BD", "pc", "30 days"), ("Tab Glimepiride", "1 mg", "OD", "ac", "30 days")], "26/10/2026", ["severe dizziness", "sweating"], ["diabetic diet", "avoid sweets"], ["regular walking"]),
    ("Sita Devi", 61, "diabetes", [("Tab Glycomet", "1000 mg", "BD", "pc", "60 days"), ("Tab Januvia", "100 mg", "OD", "pc", "60 days")], "15/11/2026", ["blurred vision", "tremors"], ["diabetic diet"], ["brisk walk 20 mins"]),
    ("Abdul Rahman", 48, "diabetes", [("Tab Forxiga", "10 mg", "OD", "pc", "30 days"), ("Tab Metformin", "500 mg", "BD", "pc", "30 days")], "05/11/2026", ["recurrent dizziness", "nausea"], ["low carbohydrate diet"], ["daily light exercise"]),
    ("Lakshmi Bai", 55, "diabetes", [("Tab Amaryl", "2 mg", "OD", "ac", "30 days"), ("Tab Metformin", "850 mg", "BD", "pc", "30 days")], "12/11/2026", ["profuse sweating", "palpitations"], ["diabetic diet"], ["avoid exertion"]),
    ("Venkatesh Rao", 64, "diabetes", [("Tab Galvus", "50 mg", "BD", "pc", "30 days"), ("Tab Metformin", "500 mg", "BD", "pc", "30 days")], "20/11/2026", ["extreme thirst", "confusion"], ["strict sugar restriction"], ["regular walking"]),
    ("Kavitha Reddy", 46, "diabetes", [("Tab Metformin", "500 mg", "BD", "pc", "45 days"), ("Tab Glimepiride", "2 mg", "OD", "ac", "45 days")], "18/11/2026", ["lightheadedness", "shivering"], ["diabetic diet"], ["light walking"]),
    ("Mohan Das", 58, "diabetes", [("Tab Januvia", "50 mg", "OD", "pc", "30 days"), ("Tab Metformin", "1000 mg", "BD", "pc", "30 days")], "25/11/2026", ["severe weakness", "dizziness"], ["diabetic diet", "avoid simple sugars"], ["brisk walk 15 mins"]),
    ("Anasuya Devi", 63, "diabetes", [("Tab Forxiga", "10 mg", "OD", "pc", "30 days"), ("Tab Glycomet", "500 mg", "TDS", "pc", "30 days")], "28/11/2026", ["frequent urination", "dehydration"], ["diabetic diet", "drink adequate water"], ["regular walking"]),
    ("Prasad Raju", 50, "diabetes", [("Tab Amaryl", "1 mg", "OD", "ac", "30 days"), ("Tab Januvia", "100 mg", "OD", "pc", "30 days")], "10/11/2026", ["cold sweats", "tremors"], ["small frequent meals", "diabetic diet"], ["morning walks"]),
    ("Saraswathi Amma", 67, "diabetes", [("Tab Metformin", "500 mg", "BD", "pc", "60 days"), ("Tab Galvus", "50 mg", "BD", "pc", "60 days")], "30/11/2026", ["drowsiness", "confusion"], ["diabetic diet"], ["light activity"]),

    # 11-20 Cardiac
    ("Krishna Murthy", 60, "cardiac", [("Tab Amlodipine", "5 mg", "OD", "pc", "30 days"), ("Tab Telmisartan", "40 mg", "OD", "pc", "30 days"), ("Tab Atorvastatin", "20 mg", "HS", "at bedtime", "30 days")], "14/11/2026", ["chest pain", "breathlessness"], ["low salt diet"], ["avoid strenuous activity"]),
    ("Subba Rao", 65, "cardiac", [("Tab Aspirin", "75 mg", "OD", "pc", "90 days"), ("Tab Clopidogrel", "75 mg", "OD", "pc", "90 days"), ("Tab Atorva", "40 mg", "HS", "at bedtime", "90 days")], "22/11/2026", ["chest pain", "bleeding gums"], ["low fat diet", "low salt diet"], ["gentle walking"]),
    ("Rajyalakshmi", 58, "cardiac", [("Tab Telma", "40 mg", "OD", "pc", "30 days"), ("Tab Lasix", "20 mg", "OD", "pc", "15 days")], "16/11/2026", ["swelling in legs", "shortness of breath"], ["fluid restriction 1.5 liters", "low salt diet"], ["bed rest as needed"]),
    ("Narayana Swamy", 72, "cardiac", [("Tab Betaloc", "25 mg", "BD", "pc", "30 days"), ("Tab Amlong", "5 mg", "OD", "pc", "30 days")], "08/11/2026", ["slow pulse", "dizziness"], ["low salt diet"], ["avoid climbing stairs"]),
    ("Padmavathi", 62, "cardiac", [("Tab Deplatt", "75 mg", "OD", "pc", "60 days"), ("Tab Storvas", "20 mg", "HS", "at bedtime", "60 days")], "19/11/2026", ["chest discomfort", "shortness of breath"], ["low cholesterol diet", "low salt diet"], ["light walking 10 mins"]),
    ("Appa Rao", 59, "cardiac", [("Tab Cresar", "40 mg", "OD", "pc", "30 days"), ("Tab Norvasc", "5 mg", "OD", "pc", "30 days")], "24/11/2026", ["severe headache", "blurred vision"], ["low salt diet"], ["moderate walking"]),
    ("Satyanarayana", 68, "cardiac", [("Tab Tenormin", "50 mg", "OD", "pc", "30 days"), ("Tab Ecosprin", "75 mg", "OD", "pc", "30 days")], "27/11/2026", ["chest heaviness", "cold sweats"], ["low salt diet"], ["avoid heavy work"]),
    ("Girija Kumari", 54, "cardiac", [("Tab Telmisartan", "80 mg", "OD", "pc", "30 days"), ("Tab Amlodipine", "10 mg", "OD", "pc", "30 days")], "06/11/2026", ["dizziness on standing", "fatigue"], ["low salt diet"], ["regular light walks"]),
    ("Ramanaiah", 66, "cardiac", [("Tab Lasix", "40 mg", "OD", "pc", "10 days"), ("Tab Atorvastatin", "10 mg", "HS", "at bedtime", "30 days")], "11/11/2026", ["breathlessness when lying flat", "chest pain"], ["restrict salt and pickles"], ["adequate bed rest"]),
    ("Vijayalakshmi", 57, "cardiac", [("Tab Deplatt", "75 mg", "OD", "pc", "90 days"), ("Tab Amlong", "5 mg", "OD", "pc", "90 days")], "29/11/2026", ["chest tightness", "bruising"], ["heart healthy diet", "low salt diet"], ["light strolls"]),

    # 21-30 Respiratory
    ("Srinivasa Rao", 45, "respiratory", [("Inhaler Salbutamol", "100 mcg", "SOS", "when needed", "30 days"), ("Tab Montelukast", "10 mg", "HS", "at bedtime", "30 days")], "04/11/2026", ["severe wheezing", "shortness of breath"], ["avoid cold drinks"], ["avoid dust exposure"]),
    ("Bhanumathi", 52, "respiratory", [("Inhaler Budecort", "200 mcg", "BD", "inhalation", "30 days"), ("Tab Deriphyllin", "150 mg", "BD", "pc", "14 days")], "13/11/2026", ["chest tightness", "persistent cough"], ["warm fluids", "adequate hydration"], ["steam inhalation twice daily"]),
    ("Chandra Sekhar", 49, "respiratory", [("Tab Azithral", "500 mg", "OD", "pc", "5 days"), ("Tab Deriphyllin", "300 mg", "BD", "pc", "7 days")], "03/11/2026", ["high fever", "yellow sputum"], ["plenty of warm water"], ["rest at home"]),
    ("Hemalatha", 38, "respiratory", [("Tab Montair", "10 mg", "HS", "at bedtime", "15 days"), ("Inhaler Salbutamol", "100 mcg", "SOS", "when needed", "15 days")], "17/11/2026", ["inability to speak full sentences", "severe breathlessness"], ["avoid cold foods"], ["breathing exercises"]),
    ("Nageswara Rao", 63, "respiratory", [("Inhaler Budecort", "400 mcg", "BD", "inhalation", "60 days"), ("Tab Deriphyllin", "150 mg", "BD", "pc", "14 days")], "21/11/2026", ["blue lips or fingers", "severe breathlessness"], ["nutritious warm diet"], ["avoid smoke and pollution"]),
    ("Sujatha", 41, "respiratory", [("Tab Azithromycin", "500 mg", "OD", "pc", "3 days"), ("Tab Montelukast", "10 mg", "HS", "at bedtime", "10 days")], "09/11/2026", ["worsening cough", "high fever"], ["warm nutritious soup", "soft diet"], ["adequate rest"]),
    ("Koteswara Rao", 56, "respiratory", [("Inhaler Asthalin", "100 mcg", "SOS", "when needed", "30 days"), ("Tab Deriphyllin", "300 mg", "BD", "pc", "10 days")], "18/11/2026", ["severe breathlessness", "chest congestion"], ["avoid oily and cold items"], ["avoid strenuous exercise"]),
    ("Radha Rani", 47, "respiratory", [("Inhaler Budecort", "200 mcg", "BD", "inhalation", "30 days"), ("Tab Montair", "10 mg", "HS", "at bedtime", "30 days")], "23/11/2026", ["wheezing not relieved by inhaler", "shortness of breath"], ["warm liquids"], ["deep breathing exercises"]),
    ("Tirupathi Rao", 51, "respiratory", [("Tab Azithral", "500 mg", "OD", "pc", "3 days"), ("Inhaler Asthalin", "100 mcg", "SOS", "when needed", "14 days")], "07/11/2026", ["chest pain on deep breath", "high fever"], ["adequate hydration"], ["rest in well ventilated room"]),
    ("Anuradha", 43, "respiratory", [("Tab Deriphyllin", "150 mg", "BD", "pc", "14 days"), ("Tab Montelukast", "10 mg", "HS", "at bedtime", "14 days")], "15/11/2026", ["severe nighttime cough", "breathlessness"], ["warm water intake"], ["avoid physical exertion"]),

    # 31-40 Post-Op / Surgical / Infection
    ("Suresh Babu", 36, "post_op", [("Tab Augmentin", "625 mg", "BD", "pc", "5 days"), ("Tab Paracetamol", "650 mg", "TDS", "pc", "3 days"), ("Tab Pantoprazole", "40 mg", "OD", "ac", "5 days")], "24/10/2026", ["wound redness", "high fever", "pus discharge"], ["high protein diet"], ["avoid heavy lifting for 4 weeks"]),
    ("Mallikarjun", 42, "post_op", [("Tab Voveran", "50 mg", "BD", "pc", "5 days"), ("Tab Calpol", "500 mg", "TDS", "pc", "3 days"), ("Tab Pan", "40 mg", "OD", "ac", "7 days")], "28/10/2026", ["severe wound pain", "bleeding from dressing"], ["soft diet"], ["bed rest for 5 days"]),
    ("Ranganayakulu", 55, "post_op", [("Tab Ultracet", "325 mg", "TDS", "pc", "3 days"), ("Tab Pantocid", "40 mg", "OD", "ac", "5 days"), ("Tab Cefixime", "200 mg", "BD", "pc", "5 days")], "31/10/2026", ["wound swelling", "fever above 101 F"], ["light nutritious diet"], ["avoid bending or lifting"]),
    ("Chandrakala", 39, "post_op", [("Tab Moxikind-CV", "625 mg", "BD", "pc", "5 days"), ("Tab Dolo", "650 mg", "TDS", "pc", "4 days"), ("Tab Omez", "20 mg", "OD", "ac", "7 days")], "29/10/2026", ["persistent vomiting", "wound gaping"], ["soft easily digestible diet"], ["strictly no heavy work"]),
    ("Brahmaiah", 61, "post_op", [("Tab Zifi", "200 mg", "BD", "pc", "7 days"), ("Tab Paracetamol", "650 mg", "SOS", "when needed", "5 days"), ("Tab Pantoprazole", "40 mg", "OD", "ac", "7 days")], "02/11/2026", ["chills and fever", "foul smelling discharge"], ["high protein diet", "drink clean water"], ["gentle mobilization"]),
    ("Geetha Vani", 44, "post_op", [("Tab Augmentin", "625 mg", "BD", "pc", "5 days"), ("Tab Voveran", "50 mg", "BD", "pc", "3 days"), ("Tab Pan", "40 mg", "OD", "ac", "5 days")], "27/10/2026", ["severe abdominal pain", "vomiting"], ["soft diet"], ["avoid strenuous activities"]),
    ("Samba Siva Rao", 50, "post_op", [("Tab Ciprogut", "500 mg", "BD", "pc", "5 days"), ("Tab Calpol", "500 mg", "TDS", "pc", "3 days"), ("Tab Rantac", "150 mg", "BD", "ac", "7 days")], "30/10/2026", ["burning urination", "high fever"], ["plenty of fluids"], ["complete bed rest"]),
    ("Parvathi", 48, "post_op", [("Tab Ultracet", "325 mg", "BD", "pc", "3 days"), ("Tab Pantocid", "40 mg", "OD", "ac", "5 days")], "26/10/2026", ["excessive bleeding", "fainting"], ["balanced nutritious diet"], ["avoid lifting weights"]),
    ("Veeraiah", 53, "post_op", [("Tab Moxikind-CV", "625 mg", "BD", "pc", "6 days"), ("Tab Dolo", "650 mg", "TDS", "pc", "3 days")], "01/11/2026", ["wound redness", "wound discharge"], ["high protein diet"], ["avoid heavy exertion"]),
    ("Shanthi Priya", 35, "post_op", [("Tab Augmentin", "625 mg", "BD", "pc", "5 days"), ("Tab Paracetamol", "500 mg", "TDS", "pc", "3 days"), ("Tab Pan", "40 mg", "OD", "ac", "5 days")], "25/10/2026", ["high fever", "severe incision pain"], ["soft home cooked meals"], ["rest at home"]),

    # 41-50 Maternity
    ("Swapna", 24, "maternity", [("Tab Folvite", "5 mg", "OD", "pc", "30 days"), ("Tab Shelcal", "500 mg", "BD", "pc", "30 days"), ("Tab Orofer-XT", "100 mg", "OD", "pc", "30 days")], "28/10/2026", ["heavy vaginal bleeding", "severe lower abdominal pain"], ["high iron diet", "adequate fluids"], ["avoid heavy domestic chores"]),
    ("Sirisha", 27, "maternity", [("Tab Labetalol", "100 mg", "BD", "pc", "14 days"), ("Tab Shelcal", "500 mg", "OD", "pc", "30 days")], "04/11/2026", ["severe headache", "blurred vision"], ["low salt diet"], ["adequate rest, avoid stress"]),
    ("Mounika", 23, "maternity", [("Tab Gestofit", "200 mg", "HS", "at bedtime", "14 days"), ("Tab Folvite", "5 mg", "OD", "pc", "30 days")], "06/11/2026", ["bleeding or spotting", "severe cramps"], ["nutritious balanced diet"], ["strict bed rest"]),
    ("Divya Vani", 29, "maternity", [("Tab Orofer-XT", "100 mg", "OD", "pc", "30 days"), ("Tab Shelcal", "500 mg", "BD", "pc", "30 days")], "10/11/2026", ["fever with chills", "foul smelling lochia"], ["protein and iron rich diet"], ["normal light walking"]),
    ("Pooja Reddy", 26, "maternity", [("Tab Labetalol", "100 mg", "TDS", "pc", "14 days"), ("Tab Shelcal", "500 mg", "OD", "pc", "30 days")], "02/11/2026", ["epigastric pain", "visual disturbances"], ["low salt diet"], ["rest in left lateral position"]),
    ("Deepika", 25, "maternity", [("Tab Folvite", "5 mg", "OD", "pc", "45 days"), ("Tab Shelcal", "500 mg", "BD", "pc", "45 days"), ("Tab Orofer-XT", "100 mg", "OD", "pc", "45 days")], "12/11/2026", ["calf pain or swelling", "heavy bleeding"], ["green leafy vegetables", "milk"], ["light mobilization"]),
    ("Kalyani", 28, "maternity", [("Tab Gestofit", "200 mg", "HS", "at bedtime", "21 days"), ("Tab Shelcal", "500 mg", "OD", "pc", "30 days")], "08/11/2026", ["severe abdominal cramps", "bleeding"], ["soft nutritious food"], ["bed rest"]),
    ("Anusha", 22, "maternity", [("Tab Orofer-XT", "100 mg", "OD", "pc", "60 days"), ("Tab Folvite", "5 mg", "OD", "pc", "60 days")], "16/11/2026", ["extreme pale skin", "breathlessness"], ["iron rich diet with jaggery"], ["avoid strenuous work"]),
    ("Swathi", 30, "maternity", [("Tab Labil", "100 mg", "BD", "pc", "14 days"), ("Tab Shelcal", "500 mg", "BD", "pc", "30 days")], "05/11/2026", ["swelling of face and hands", "headache"], ["low salt diet"], ["adequate bed rest"]),
    ("Tejaswi", 26, "maternity", [("Tab Folvite", "5 mg", "OD", "pc", "30 days"), ("Tab Shelcal", "500 mg", "BD", "pc", "30 days")], "14/11/2026", ["persistent high fever", "severe pain"], ["nutritious diet", "plenty of water"], ["gradual return to normal activity"])
]

dataset = []
for i, (name, age, cat, meds, fu_date, warnings, diet, activity) in enumerate(cases):
    lines = [
        "DISCHARGE SUMMARY",
        f"Patient Name: {name} Age: {age}",
        f"Condition: {cat.replace('_', ' ').title()}",
        "Medications:"
    ]
    for med in meds:
        mname, mdose, mfreq, mtime, mdur = med
        lines.append(f"{mname} {mdose} {mfreq} {mtime} x {mdur}")
    lines.append(f"Follow-up: Review in OPD on {fu_date}")
    lines.append(f"Warning signs: {', '.join(warnings)}")
    lines.append(f"Diet: {', '.join(diet)}")
    lines.append(f"Activity: {', '.join(activity)}")

    summary_text = "\n".join(lines)

    d_parts = fu_date.split("/")
    iso_date = f"{d_parts[2]}-{int(d_parts[1]):02d}-{int(d_parts[0]):02d}"

    dataset.append({
        "id": i + 1,
        "name": name,
        "age": age,
        "category": cat,
        "summary": summary_text,
        "expected_med_count": len(meds),
        "expected_date": iso_date
    })

out_path = Path("data/samples/gold_50.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"Generated {len(dataset)} gold summaries in {out_path}")
