from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
import io


def generate_pdf(resume_text: str, user_name: str = 'Resume') -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=14*mm, bottomMargin=14*mm
    )

    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    heading_style = ParagraphStyle(
        'SecHeading', fontSize=9, fontName='Helvetica-Bold',
        textColor=colors.black, spaceBefore=8, spaceAfter=3,
        borderPadding=(0, 0, 2, 0), leading=12,
        textTransform='uppercase', letterSpacing=1
    )
    body_style = ParagraphStyle(
        'Body', fontSize=10, fontName='Helvetica',
        textColor=colors.HexColor('#222222'),
        spaceAfter=2, leading=14
    )
    bullet_style = ParagraphStyle(
        'Bullet', fontSize=10, fontName='Helvetica',
        textColor=colors.HexColor('#222222'),
        leftIndent=12, spaceAfter=2, leading=13,
        bulletIndent=0
    )
    name_style = ParagraphStyle(
        'Name', fontSize=20, fontName='Helvetica-Bold',
        alignment=TA_CENTER, textColor=colors.black,
        spaceAfter=4, leading=24
    )
    contact_style = ParagraphStyle(
        'Contact', fontSize=9, fontName='Helvetica',
        alignment=TA_CENTER, textColor=colors.HexColor('#444444'),
        spaceAfter=10, leading=12
    )

    lines = resume_text.strip().split('\n')
    first_line = True
    second_line = True

    for line in lines:
        s = line.strip()
        if not s:
            story.append(Spacer(1, 4))
            continue

        # First non-empty line = name
        if first_line:
            story.append(Paragraph(s, name_style))
            # Add horizontal rule
            from reportlab.platypus import HRFlowable
            story.append(HRFlowable(width='100%', thickness=1, color=colors.black, spaceAfter=4))
            first_line = False
            second_line = True
            continue

        # Section headings — ALL CAPS short lines
        if s.isupper() and len(s) > 2 and len(s) < 40:
            from reportlab.platypus import HRFlowable
            story.append(Spacer(1, 4))
            story.append(Paragraph(s, heading_style))
            story.append(HRFlowable(width='100%', thickness=1, color=colors.black, spaceAfter=4))
            continue

        # Bullet points
        if s.startswith(('•', '-', '*', '·')):
            clean = s.lstrip('•-*· ').strip()
            story.append(Paragraph(f'• {clean}', bullet_style))
            continue

        # Regular lines
        story.append(Paragraph(s, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
