# CareBridge Discharge Summary Ingestion & Normalization
# Implements PRD Section 7 (Component 1) and FR-1, FR-2

import hashlib
import re
from typing import Dict, List, NamedTuple, Tuple


class SectionBoundary(NamedTuple):
    title: str
    start: int
    end: int
    content: str


class IngestResult(NamedTuple):
    clean_text: str
    source_hash: str
    sections: Dict[str, SectionBoundary]


# Common clinical section header identifiers
SECTION_PATTERNS = {
    "patient_info": r"(?:patient\s+details|patient\s+info|demographics|patient\s+name|admission\s+details)",
    "diagnosis": r"(?:diagnosis|final\s+diagnosis|provisional\s+diagnosis|condition)",
    "medications": r"(?:medications|discharge\s+medications|treatment\s+given|rx|medication\s+table|medicines)",
    "warning_signs": r"(?:warning\s+signs?|red\s+flags?|emergency\s+signs?|when\s+to\s+return|seek\s+medical\s+help)",
    "diet": r"(?:diet|dietary\s+advice|nutrition|what\s+to\s+eat)",
    "activity": r"(?:activity|exercise|rest|precautions|physical\s+activity)",
    "follow_up": r"(?:follow[- ]?up|review|next\s+visit|appointment|opd\s+schedule)",
}


def clean_source_text(raw_text: str) -> str:
    # Cleans trailing whitespace, normalizes carriage returns, preserves exact casing and characters
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip()


def compute_source_hash(text: str) -> str:
    # Computes canonical SHA-256 hash of the input text
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_sections(text: str) -> Dict[str, SectionBoundary]:
    # Identifies section headers and maps their character spans
    sections: Dict[str, SectionBoundary] = {}
    lines = text.splitlines(keepends=True)

    header_matches: List[Tuple[str, int, int]] = []
    current_offset = 0

    for line in lines:
        line_len = len(line)
        stripped = line.strip()
        for sec_name, pattern in SECTION_PATTERNS.items():
            if re.match(rf"^(?:#+\s*)?{pattern}[:\-]?\s*$", stripped, re.IGNORECASE):
                header_matches.append((sec_name, current_offset, current_offset + line_len))
                break
        current_offset += line_len

    if not header_matches:
        # Fallback: Treat entire text as general section
        sections["general"] = SectionBoundary(title="general", start=0, end=len(text), content=text)
        return sections

    # Assign boundaries between consecutive headers
    for i, (sec_name, start_idx, header_end) in enumerate(header_matches):
        next_start = header_matches[i + 1][1] if i + 1 < len(header_matches) else len(text)
        content = text[header_end:next_start].strip()
        sections[sec_name] = SectionBoundary(
            title=sec_name,
            start=start_idx,
            end=next_start,
            content=content,
        )

    return sections


def ingest(raw_text: str) -> IngestResult:
    # Full ingestion pipeline
    clean = clean_source_text(raw_text)
    source_hash = compute_source_hash(clean)
    sections = split_sections(clean)
    return IngestResult(clean_text=clean, source_hash=source_hash, sections=sections)
