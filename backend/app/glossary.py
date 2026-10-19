# CareBridge Data Loader: Abbreviations Glossary, Drug Table, and Template Libraries
# Implements PRD Section 7, 8, 9.2, and 12

import csv
import json
from pathlib import Path
from typing import Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Cached in-memory datasets
_ABBREVIATIONS = {}
_DRUG_TABLE = {}
_PHRASES_EN = {}
_PHRASES_TE = {}


def _init_data():
    global _ABBREVIATIONS, _DRUG_TABLE, _PHRASES_EN, _PHRASES_TE
    if _ABBREVIATIONS:
        return

    # 1. Load clinical abbreviations
    glossary_path = DATA_DIR / "glossary.json"
    if glossary_path.exists():
        with open(glossary_path, "r", encoding="utf-8") as f:
            _ABBREVIATIONS = json.load(f).get("abbreviations", {})

    # 2. Load drug table (brand -> generic & transliteration)
    drug_path = DATA_DIR / "drug_table.csv"
    if drug_path.exists():
        with open(drug_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row["brand_name"].strip().lower()
                generic = row["generic_name"].strip()
                _DRUG_TABLE[brand] = {
                    "generic_name": generic,
                    "default_form": row.get("default_form", "tablet"),
                    "default_route": row.get("default_route", "oral"),
                    "telugu_transliteration": row.get("telugu_transliteration", generic),
                    "category": row.get("category", "general"),
                }
                # Also index generic name in lowercase
                gen_key = generic.lower()
                if gen_key not in _DRUG_TABLE:
                    _DRUG_TABLE[gen_key] = _DRUG_TABLE[brand]

    # 3. Load English phrases
    phrases_en_path = DATA_DIR / "phrases_en.json"
    if phrases_en_path.exists():
        with open(phrases_en_path, "r", encoding="utf-8") as f:
            _PHRASES_EN = json.load(f)

    # 4. Load Telugu phrases
    phrases_te_path = DATA_DIR / "phrases_te.json"
    if phrases_te_path.exists():
        with open(phrases_te_path, "r", encoding="utf-8") as f:
            _PHRASES_TE = json.load(f)


_init_data()


def get_abbreviation(token: str) -> Optional[dict]:
    # Looks up clinical short form case-insensitively
    _init_data()
    return _ABBREVIATIONS.get(token.strip().upper())


def expand_frequency(token: str) -> Tuple[str, str, str, bool, Optional[str]]:
    # Returns (code, plain_en, plain_te, is_ambiguous, ambiguity_note)
    _init_data()
    item = get_abbreviation(token)
    if not item:
        # Unknown short form: does not guess, returns code as-is with ambiguity flag
        clean = token.strip()
        return (clean, clean, clean, True, f"Unrecognized frequency code '{clean}'")

    code = item.get("code", token.upper())
    plain_en = item.get("plain_en", token)
    plain_te = item.get("plain_te", token)
    is_ambiguous = item.get("is_ambiguous", False)
    note = item.get("ambiguity_note")
    return (code, plain_en, plain_te, is_ambiguous, note)


def expand_timing(token: str) -> Tuple[Optional[str], Optional[str]]:
    # Returns (timing_en, timing_te)
    _init_data()
    item = get_abbreviation(token)
    if item:
        return (item.get("plain_en"), item.get("plain_te"))
    return (None, None)


def resolve_drug(name_as_written: str) -> Tuple[str, Optional[str], Optional[str], str]:
    # Resolves medicine name against drug table.
    # Returns (generic_name, form, route, telugu_transliteration)
    _init_data()
    cleaned = name_as_written.strip()
    import re
    m = re.match(r"^(?:Tab|Tablet|Cap|Capsule|Inj|Injection|Syp|Syrup|Susp|Oint|Drops|Eye Drops|Inhaler)\s+(.+)$", cleaned, re.I)
    form = None
    route = "oral"
    if m:
        prefix = cleaned[:m.start(1)].strip().lower()
        if "tab" in prefix:
            form = "tablet"
        elif "cap" in prefix:
            form = "capsule"
        elif "inj" in prefix:
            form = "injection"
            route = "injectable"
        elif "syp" in prefix or "susp" in prefix:
            form = "syrup"
        elif "inhal" in prefix:
            form = "inhaler"
            route = "inhaled"
        elif "drop" in prefix:
            form = "drops"
            route = "ophthalmic" if "eye" in prefix else "topical"
        cleaned_name = m.group(1).strip()
    else:
        cleaned_name = cleaned

    lookup_key = cleaned_name.lower()
    entry = _DRUG_TABLE.get(lookup_key)
    if entry:
        return (
            entry["generic_name"],
            form or entry.get("default_form", "tablet"),
            entry.get("default_route", "oral"),
            entry.get("telugu_transliteration", entry["generic_name"]),
        )

    # Fallback if molecule not in table: preserve exact name
    return (cleaned_name, form or "tablet", "oral", cleaned_name)


def get_phrase(section: str, key: str, lang: str = "en") -> str:
    # Retrieves template or section phrase from library
    _init_data()
    store = _PHRASES_TE if lang == "te" else _PHRASES_EN
    sec_dict = store.get(section, {})
    return sec_dict.get(key, key)


def transliterate_drug(generic_name: str) -> str:
    # Returns Telugu script transliteration of drug name
    _init_data()
    entry = _DRUG_TABLE.get(generic_name.strip().lower())
    if entry:
        return entry.get("telugu_transliteration", generic_name)
    return generic_name
