# CareBridge Single-Page Fridge Sheet PDF Builder
# Implements PRD Section 5, 8, 12, 13.2, 19, and FR-12

from io import BytesIO
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .glossary import transliterate_drug
from .schema import CarePlan

FONT_PATH = Path(__file__).resolve().parent.parent / "data" / "fonts" / "NotoSansTelugu-Regular.ttf"
TELUGU_FONT_REGISTERED = False


def _register_telugu_font():
    global TELUGU_FONT_REGISTERED
    if TELUGU_FONT_REGISTERED:
        return
    if FONT_PATH.exists():
        try:
            pdfmetrics.registerFont(TTFont("NotoSansTelugu", str(FONT_PATH)))
            TELUGU_FONT_REGISTERED = True
        except Exception:
            TELUGU_FONT_REGISTERED = False


def _map_to_time_blocks(freq_code: str, timing: Optional[str] = None) -> tuple:
    # Maps medication frequency and timing to (morning, afternoon, night, bedtime, note)
    f = (freq_code or "").upper()
    t = (timing or "").lower()

    morning, afternoon, night, bedtime = "-", "-", "-", "-"
    note = "with food" if "with" in t else ("after food" if "pc" in t or "after" in t else ("before food" if "ac" in t or "before" in t else ""))

    if f in ["BD", "BID"]:
        morning = "✓ 1"
        night = "✓ 1"
    elif f in ["TDS", "TID"]:
        morning = "✓ 1"
        afternoon = "✓ 1"
        night = "✓ 1"
    elif f == "QID":
        morning = "✓ 1"
        afternoon = "✓ 1"
        night = "✓ 1"
        bedtime = "✓ 1"
    elif f == "HS":
        bedtime = "✓ 1"
    elif f in ["OD", "QD"]:
        if "bedtime" in t:
            bedtime = "✓ 1"
        else:
            morning = "✓ 1"
    elif f in ["SOS", "PRN"]:
        note = "Only when needed"
    else:
        morning = "As directed"

    return morning, afternoon, night, bedtime, note


def build_fridge_sheet_pdf(plan: CarePlan, lang: str = "both") -> bytes:
    # Builds an A4 single-page patient care fridge sheet.
    # High-contrast, time-block grid, red emergency warning box, embedded Telugu font.
    _register_telugu_font()
    font_name = "NotoSansTelugu" if TELUGU_FONT_REGISTERED else "Helvetica"
    font_bold = font_name

    out = BytesIO()
    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=24,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CareBridgeTitle",
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0D5C3A"),
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "CareBridgeSubtitle",
        fontName=font_name,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
    )
    th_style = ParagraphStyle(
        "CareBridgeTH",
        fontName=font_bold,
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )
    td_style = ParagraphStyle(
        "CareBridgeTD",
        fontName=font_name,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1A202C"),
    )
    td_center = ParagraphStyle(
        "CareBridgeTDCenter",
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1A202C"),
        alignment=1,
    )
    alert_title = ParagraphStyle(
        "CareBridgeAlertTitle",
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#C53030"),
    )
    alert_body = ParagraphStyle(
        "CareBridgeAlertBody",
        fontName=font_name,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2D3748"),
    )
    footer_style = ParagraphStyle(
        "CareBridgeFooter",
        fontName=font_name,
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#718096"),
        alignment=1,
    )

    story = []

    # 1. Header banner
    p_name = plan.patient.name if plan.patient and plan.patient.name else "Patient"
    p_age = f", Age: {plan.patient.age}" if plan.patient and plan.patient.age else ""
    fu_date = plan.follow_ups[0].date if plan.follow_ups else "As advised"
    fu_dept = plan.follow_ups[0].department if plan.follow_ups and plan.follow_ups[0].department else "OPD"

    story.append(Paragraph("CareBridge — Patient Care Fridge Sheet", title_style))
    story.append(Paragraph(
        f"<b>Patient:</b> {p_name}{p_age} | <b>Next OPD Visit:</b> {fu_date} ({fu_dept}) | <b>Hospital Helpline:</b> 108 / 104",
        subtitle_style,
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0D5C3A"), spaceAfter=10))

    # 2. Medication 4-Time-Block Table Grid
    table_data = [
        [
            Paragraph("<b>Medicine<br/>మందు పేరు</b>", th_style),
            Paragraph("<b>Dose<br/>మోతాదు</b>", th_style),
            Paragraph("<b>Morning<br/>ఉదయం</b>", th_style),
            Paragraph("<b>Afternoon<br/>మధ్యాహ్నం</b>", th_style),
            Paragraph("<b>Night<br/>రాత్రి</b>", th_style),
            Paragraph("<b>Bedtime<br/>పడుకునేముందు</b>", th_style),
            Paragraph("<b>Instructions<br/>సూచనలు</b>", th_style),
        ]
    ]

    for med in plan.medicines:
        m, a, n, b, note = _map_to_time_blocks(med.frequency_code, med.timing)
        te_translit = transliterate_drug(med.name_generic)
        med_label = f"<b>{med.name_generic}</b>"
        if te_translit != med.name_generic and lang in ["te", "both"]:
            med_label += f"<br/><font color='#4A5568'>{te_translit}</font>"

        dur_text = f", for {med.duration}" if med.duration else ""
        timing_note = f"{note}{dur_text}".strip(", ")

        table_data.append([
            Paragraph(med_label, td_style),
            Paragraph(f"<b>{med.dose}</b>", td_center),
            Paragraph(m, td_center),
            Paragraph(a, td_center),
            Paragraph(n, td_center),
            Paragraph(b, td_center),
            Paragraph(timing_note or "-", td_style),
        ])

    med_table = Table(
        table_data,
        colWidths=[140, 55, 60, 60, 55, 65, 104],
        repeatRows=1,
    )
    med_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D5C3A")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(med_table)
    story.append(Spacer(1, 10))

    # 3. Red Warning Alert Box (EMERGENCY)
    warnings_en = [w.text_source for w in plan.warning_signs] or ["severe dizziness", "chest pain", "shortness of breath", "high fever"]
    warnings_str = ", ".join(warnings_en)

    alert_box_data = [
        [
            Paragraph("<b>EMERGENCY / అత్యవసర సంకేతాలు: GO TO HOSPITAL AT ONCE IF:</b>", alert_title),
        ],
        [
            Paragraph(
                f"Seek immediate medical attention if you experience: <b>{warnings_str}</b>. Call hospital emergency or 108.",
                alert_body,
            ),
        ]
    ]
    alert_table = Table(alert_box_data, colWidths=[539])
    alert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF5F5")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#E53E3E")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(alert_table)
    story.append(Spacer(1, 10))

    # 4. Diet & Activity Box
    diet_str = "; ".join(d.text_source for d in plan.diet) if plan.diet else "Normal balanced diet"
    act_str = "; ".join(a.text_source for a in plan.activity) if plan.activity else "Adequate rest, avoid sudden exertion"

    guide_data = [
        [
            Paragraph("<b>Diet / ఆహార నియమాలు:</b>", td_style),
            Paragraph(diet_str, td_style),
        ],
        [
            Paragraph("<b>Activity / విశ్రాంతి:</b>", td_style),
            Paragraph(act_str, td_style),
        ],
        [
            Paragraph("<b>Follow-up / సందర్శన:</b>", td_style),
            Paragraph(f"Please visit <b>{fu_dept}</b> on <b>{fu_date}</b> for clinical review.", td_style),
        ]
    ]
    guide_table = Table(guide_data, colWidths=[120, 419])
    guide_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(guide_table)
    story.append(Spacer(1, 12))

    # 5. Footer & Safety Boundary
    story.append(Paragraph(
        "CareBridge Verified Care Plan | Team BALLERINA | Hackathon Prototype — Requires authorized clinical review prior to patient release.",
        footer_style,
    ))

    doc.build(story)
    return out.getvalue()
