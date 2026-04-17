from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime


# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#1a4a7a")
BLUE_MID    = colors.HexColor("#2b6cb0")
BLUE_LIGHT  = colors.HexColor("#ebf8ff")
AMBER       = colors.HexColor("#ed8936")
AMBER_LIGHT = colors.HexColor("#fffbeb")
RED_DARK    = colors.HexColor("#c53030")
RED_LIGHT   = colors.HexColor("#fff5f5")
GREEN_DARK  = colors.HexColor("#276749")
GREEN_LIGHT = colors.HexColor("#f0fff4")
GRAY_DARK   = colors.HexColor("#4a5568")
GRAY_LIGHT  = colors.HexColor("#f7fafc")
BORDER      = colors.HexColor("#e2e8f0")
WHITE       = colors.white


def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=20,
            textColor=BLUE_DARK, spaceAfter=2, alignment=TA_LEFT
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica", fontSize=10,
            textColor=GRAY_DARK, spaceAfter=0, alignment=TA_LEFT
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=11,
            textColor=BLUE_MID, spaceBefore=14, spaceAfter=6,
            borderPad=2
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9,
            textColor=GRAY_DARK, leading=14, spaceAfter=4
        ),
        "body_bold": ParagraphStyle(
            "body_bold", fontName="Helvetica-Bold", fontSize=9,
            textColor=GRAY_DARK, leading=14
        ),
        "small": ParagraphStyle(
            "small", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#718096"), leading=12
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", fontName="Helvetica-Oblique", fontSize=8,
            textColor=colors.HexColor("#744210"), leading=12,
            backColor=AMBER_LIGHT, borderPad=6
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.HexColor("#a0aec0"), spaceAfter=2
        ),
        "drug_name": ParagraphStyle(
            "drug_name", fontName="Helvetica-Bold", fontSize=11,
            textColor=BLUE_DARK
        ),
        "drug_role": ParagraphStyle(
            "drug_role", fontName="Helvetica-Bold", fontSize=8,
            textColor=BLUE_MID
        ),
        "warning": ParagraphStyle(
            "warning", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#744210"), leading=12
        ),
        "emergency": ParagraphStyle(
            "emergency", fontName="Helvetica-Bold", fontSize=10,
            textColor=WHITE, leading=14
        ),
    }
    return styles


def severity_color(level: str):
    if level == "Mild":
        return GREEN_DARK, GREEN_LIGHT
    elif level == "Moderate":
        return AMBER, AMBER_LIGHT
    elif level.startswith("Severe"):
        return RED_DARK, RED_LIGHT
    return GRAY_DARK, GRAY_LIGHT


def generate_pdf(report_data: dict) -> bytes:
    """
    Generate a professional A4 PDF report from the prediction result.
    Returns raw PDF bytes.
    """

    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm,  bottomMargin=18*mm
    )

    S       = build_styles()
    story   = []
    W       = A4[0] - 36*mm   # usable width

    now     = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # ── HEADER ──────────────────────────────────────────
    header_data = [[
        Paragraph("Drug Recommendation System", S["title"]),
        Paragraph(f"Generated: {now}", ParagraphStyle(
            "ts", fontName="Helvetica", fontSize=8,
            textColor=GRAY_DARK, alignment=TA_RIGHT
        ))
    ]]
    header_table = Table(header_data, colWidths=[W*0.65, W*0.35])
    header_table.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "BOTTOM"),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]))
    story.append(header_table)
    story.append(Paragraph("Symptom-based disease diagnosis and safe drug recommendation", S["subtitle"]))
    story.append(HRFlowable(width=W, thickness=1.5, color=BLUE_MID, spaceAfter=10))

    # ── PATIENT PROFILE ──────────────────────────────────
    profile = report_data.get("profile", {})
    age_group = profile.get("age_group", "adult").capitalize()
    gender    = profile.get("gender", "unspecified").capitalize()
    allergy   = profile.get("allergy", "none").capitalize()
    symptoms  = report_data.get("symptoms", [])

    profile_rows = [
        [
            Paragraph("AGE GROUP", S["label"]),
            Paragraph("GENDER", S["label"]),
            Paragraph("ALLERGY", S["label"]),
            Paragraph("SYMPTOMS ENTERED", S["label"]),
        ],
        [
            Paragraph(age_group, S["body_bold"]),
            Paragraph(gender, S["body_bold"]),
            Paragraph(allergy, S["body_bold"]),
            Paragraph(", ".join([s.replace("_"," ") for s in symptoms]) or "—", S["body"]),
        ]
    ]
    profile_table = Table(profile_rows, colWidths=[W*0.15, W*0.15, W*0.15, W*0.55])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), GRAY_LIGHT),
        ("GRID",         (0,0), (-1,-1), 0.5, BORDER),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 10))

    # ── EMERGENCY BANNER ─────────────────────────────────
    if report_data.get("emergency"):
        emergency_data = [[
            Paragraph(
                "EMERGENCY WARNING: Your symptoms indicate a potentially serious condition. "
                "Please seek immediate medical attention or go to the nearest hospital.",
                S["emergency"]
            )
        ]]
        em_table = Table(emergency_data, colWidths=[W])
        em_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), RED_DARK),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
            ("LEFTPADDING",  (0,0), (-1,-1), 12),
            ("ROUNDEDCORNERS", [4]),
        ]))
        story.append(em_table)
        story.append(Spacer(1, 10))

    # ── DIAGNOSIS ────────────────────────────────────────
    story.append(Paragraph("Diagnosis", S["section"]))

    disease    = report_data.get("disease", "—")
    confidence = report_data.get("confidence", "—")
    conf_warn  = report_data.get("confidence_warning")

    diag_data = [[
        Paragraph("PREDICTED DISEASE", S["label"]),
        Paragraph("CONFIDENCE", S["label"]),
    ],[
        Paragraph(disease, ParagraphStyle(
            "dn", fontName="Helvetica-Bold", fontSize=14, textColor=BLUE_DARK
        )),
        Paragraph(confidence, ParagraphStyle(
            "cn", fontName="Helvetica-Bold", fontSize=14, textColor=BLUE_MID
        )),
    ]]
    diag_table = Table(diag_data, colWidths=[W*0.7, W*0.3])
    diag_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), BLUE_LIGHT),
        ("GRID",         (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
    ]))
    story.append(diag_table)

    if conf_warn:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Note: {conf_warn}", S["warning"]))

    # ── DIFFERENTIAL DIAGNOSES ───────────────────────────
    top3 = report_data.get("top3", [])
    if len(top3) > 1:
        story.append(Paragraph("Differential Diagnoses", S["section"]))
        diff_header = [
            Paragraph("RANK", S["label"]),
            Paragraph("CONDITION", S["label"]),
            Paragraph("CONFIDENCE", S["label"]),
        ]
        labels = ["Most likely", "2nd possibility", "3rd possibility"]
        diff_rows = [diff_header] + [
            [
                Paragraph(labels[i], S["small"]),
                Paragraph(item["disease"], S["body_bold"] if i == 0 else S["body"]),
                Paragraph(item["confidence"], S["body_bold"] if i == 0 else S["body"]),
            ]
            for i, item in enumerate(top3)
        ]
        diff_table = Table(diff_rows, colWidths=[W*0.25, W*0.5, W*0.25])
        diff_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), GRAY_LIGHT),
            ("BACKGROUND",   (0,1), (-1,1), BLUE_LIGHT),
            ("GRID",         (0,0), (-1,-1), 0.5, BORDER),
            ("TOPPADDING",   (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0), (-1,-1), 6),
            ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ]))
        story.append(diff_table)

    # ── SEVERITY ─────────────────────────────────────────
    severity = report_data.get("severity", {})
    s_level  = severity.get("level", "Unknown")
    s_score  = severity.get("score", 0)
    s_count  = severity.get("symptoms_matched", 0)
    s_fg, s_bg = severity_color(s_level)

    story.append(Paragraph("Severity Assessment", S["section"]))
    sev_data = [[
        Paragraph("LEVEL", S["label"]),
        Paragraph("SCORE", S["label"]),
        Paragraph("SYMPTOMS MATCHED", S["label"]),
    ],[
        Paragraph(s_level, ParagraphStyle(
            "sl", fontName="Helvetica-Bold", fontSize=11, textColor=s_fg
        )),
        Paragraph(str(s_score), S["body_bold"]),
        Paragraph(str(s_count), S["body_bold"]),
    ]]
    sev_table = Table(sev_data, colWidths=[W*0.4, W*0.2, W*0.4])
    sev_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), s_bg),
        ("GRID",         (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
    ]))
    story.append(sev_table)

    # ── DESCRIPTION ──────────────────────────────────────
    description = report_data.get("description", "")
    if description:
        story.append(Paragraph("About This Disease", S["section"]))
        story.append(Paragraph(description, S["body"]))

    # ── PRECAUTIONS ──────────────────────────────────────
    precautions = report_data.get("precautions", [])
    if precautions:
        story.append(Paragraph("Recommended Precautions", S["section"]))
        for i, p in enumerate(precautions, 1):
            story.append(Paragraph(f"{i}.  {p.capitalize()}", S["body"]))

    # ── TREATMENT REGIMEN ────────────────────────────────
    medication = report_data.get("medication", {})
    regimen    = medication.get("regimen", [])
    reg_note   = medication.get("note", "")
    prof_notes = medication.get("profile_notes", [])

    story.append(Paragraph("Treatment Regimen", S["section"]))
    if reg_note:
        story.append(Paragraph(reg_note, S["small"]))
        story.append(Spacer(1, 6))

    if not regimen:
        story.append(Paragraph("No safe medication found. Please consult a doctor.", S["body"]))
    else:
        drug_header = [
            Paragraph("ROLE", S["label"]),
            Paragraph("MEDICATION", S["label"]),
            Paragraph("DOSAGE", S["label"]),
            Paragraph("DURATION", S["label"]),
        ]
        drug_rows = [drug_header]
        for drug in regimen:
            drug_rows.append([
                Paragraph(drug.get("role", ""), S["small"]),
                Paragraph(drug.get("drug", ""), S["body_bold"]),
                Paragraph(drug.get("dosage", ""), S["body"]),
                Paragraph(drug.get("duration", ""), S["body"]),
            ])

        col_w = [W*0.22, W*0.22, W*0.32, W*0.24]
        drug_table = Table(drug_rows, colWidths=col_w, repeatRows=1)
        drug_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), GRAY_LIGHT),
            ("BACKGROUND",   (0,1), (-1,1), BLUE_LIGHT),
            ("ROWBACKGROUNDS",(0,2), (-1,-1), [WHITE, GRAY_LIGHT]),
            ("GRID",         (0,0), (-1,-1), 0.5, BORDER),
            ("TOPPADDING",   (0,0), (-1,-1), 7),
            ("BOTTOMPADDING",(0,0), (-1,-1), 7),
            ("LEFTPADDING",  (0,0), (-1,-1), 8),
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ]))
        story.append(drug_table)

    # ── PROFILE ADVISORY NOTES ───────────────────────────
    if prof_notes:
        story.append(Paragraph("Patient Profile Advisories", S["section"]))
        for note in prof_notes:
            note_data = [[Paragraph(note, S["warning"])]]
            note_table = Table(note_data, colWidths=[W])
            note_table.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,-1), AMBER_LIGHT),
                ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#f6ad55")),
                ("TOPPADDING",   (0,0), (-1,-1), 8),
                ("BOTTOMPADDING",(0,0), (-1,-1), 8),
                ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ]))
            story.append(note_table)
            story.append(Spacer(1, 4))

    # ── DISCLAIMER ───────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER, spaceAfter=8))
    story.append(Paragraph(
        "Medical Disclaimer: This report is generated by an AI-based system for informational purposes only. "
        "It does not constitute professional medical advice, diagnosis, or treatment. "
        "Always consult a qualified healthcare provider before starting, stopping, or changing any medication. "
        "Dosages listed are standard reference values and may need adjustment based on individual patient factors "
        "including weight, renal function, comorbidities, and clinical judgement.",
        S["disclaimer"]
    ))

    doc.build(story)
    return buffer.getvalue()