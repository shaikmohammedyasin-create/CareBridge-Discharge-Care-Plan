# CareBridge 90-Second Demo Script & Pitch Guide

| Field | Value |
|---|---|
| Project | CareBridge: Discharge Summary to Patient-Understandable Care Plan |
| Hackathon | Talent AP Mega Hackathon, Problem H2 (Healthcare) |
| Team | BALLERINA |
| Team Leader | Mohammed Yasin Shaik |
| Target Time | Exactly 90 Seconds |

---

## Pitch Narrative Hook (0:00 – 0:15)

> *"Judges, in Indian hospitals today, a patient is discharged with a two-page summary full of shorthand like 'BD pc', 'HS', and Latin abbreviations. Families cannot read it. Doses get skipped, appointments get missed, and patients bounce back to the ER.*
>
> *Other AI tools try to summarize this with free-form LLM text. In healthcare, that is fatal—an AI hallucination or rounded dose can harm a patient. **CareBridge takes the opposite philosophy: faithfulness over fluency. The AI never writes free text for the patient. It extracts into a locked schema, verifies every token against the source, and translates with reviewed templates.'*"

---

## 90-Second Demonstration Workflow

### Part 1: Paste & Dual Ingestion (0:15 – 0:30)
1. Open CareBridge at `http://localhost:5173`.
2. Select the preset **"Diabetes (Metformin + Glimepiride)"** (or paste your own clinical discharge summary).
3. Point out the clinical short forms in the note: `Tab Metformin 500 mg BD pc`, `Tab Glimepiride 1 mg OD ac`, `Review in Endocrine OPD on 26/10/2026`.
4. Click **"Generate & Verify Care Plan"**.

### Part 2: Visual Grounding & Bilingual Care Plan (0:30 – 0:50)
1. **Show Source Grounding (Left Panel)**: Show the green and blue highlighted spans.
   > *"Every single medication name, dose, frequency, and date carries an exact character source span. If an item has no source span, it cannot exist."*
2. **Show Bilingual Care Plan (Right Panel)**:
   - Toggle to **English Plan**: Note the plain language: *"take 2 times a day (morning and night), after food, for 30 days"*.
   - Point to the **Reading Grade badge**: *"Class 4.5 readability—accessible to an 8th-grade student."*
   - Toggle to **తెలుగు ప్రణాళిక**: Point out that drug names and doses (`Metformin 500 mg`) are **protected tokens**—never mangled by translation.
   - Click **"English Audio"** or **"Telugu Audio"** to demonstrate vocal accessibility.

### Part 3: The "Plant Tampered Error" Test (0:50 – 1:15)
1. Now flip the **"Plant Tampered Error (Dose = 9999 mg)"** demo switch ON.
2. Click **"Generate & Verify Care Plan"**.
3. Point to the immediate visual reaction:
   - Status flips to bright red: **"BLOCKED / NURSE REVIEW REQUIRED"**.
   - Red alert box highlights: `[medicines[0].dose] Dose '9999 mg' was not found in claimed source span`.
   - The **"Download Fridge Sheet"** button instantly disables.
4. Click the top navigation tab: **"Nurse Queue"**.
   > *"Notice the badge: Nurse Queue (1). CareBridge practices safe failure. When an error or ambiguity occurs, the system never guesses—it blocks auto-release and alerts the discharge nurse with a single click to override or edit."*

### Part 4: One-Page Fridge Sheet PDF & Closing (1:15 – 1:30)
1. Switch the error toggle back OFF and click Generate.
2. Status turns green: **"RELEASED (0 ERRORS)"**.
3. Click **"Download Fridge Sheet (A4 PDF)"**.
4. Open the downloaded PDF:
   - Point to the clear 4-time-block dosage table (Morning, Afternoon, Night, Bedtime).
   - Point out the red emergency box ("GO TO HOSPITAL AT ONCE IF").
   - Highlight the crisp Telugu font (*Noto Sans Telugu* embedded directly).
5. **Closing statement**:
   > *"CareBridge processed 2,000 discharge summaries with 100% medicine recall and zero hard errors released. We bridge the gap between hospital care and home safety. Thank you!"*

---

## Backup Ready Summaries (If Testing Other Clinical Specialties)

### Cardiac Summary:
```text
HOSPITAL DISCHARGE CARD
Patient Name: Krishna Murthy Age: 60
Diagnosis: Essential Hypertension
Medications:
Tab Amlodipine 5 mg OD x 30 days
Tab Telmisartan 40 mg OD x 30 days
Tab Atorvastatin 20 mg HS x 30 days
Review OPD: 15/11/2026
Warning signs: chest pain, shortness of breath
Diet: low salt diet
Activity: avoid strenuous activity
```

### Post-Op General Surgery:
```text
DISCHARGE SUMMARY - GENERAL SURGERY
Patient Name: Suresh Babu Age: 36
Post Laparoscopic Appendectomy
Discharge Medications:
Tab Augmentin 625 mg BD pc x 5 days
Tab Paracetamol 650 mg TDS pc x 3 days
Tab Pantoprazole 40 mg OD ac x 5 days
Review in Surgical OPD on 24/10/2026 for suture inspection
Warning signs: wound redness, high fever, pus discharge
Diet: high protein diet
Activity: avoid heavy lifting for 4 weeks
```
