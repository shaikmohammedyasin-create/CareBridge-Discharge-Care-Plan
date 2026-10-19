from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def make_pdf(english: str, telugu: str) -> bytes:
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("CareBridge — Patient Care Plan", styles["Title"]),
        Spacer(1, 12),
        Paragraph(english.replace("\n", "<br/>"), styles["BodyText"]),
        Spacer(1, 18),
        Paragraph("Telugu Care Plan", styles["Heading2"]),
        Paragraph(telugu.replace("\n", "<br/>"), styles["BodyText"]),
    ]
    doc.build(story)
    return out.getvalue()
