from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime

# ── COLOURS ──────────────────────────────────────────────────────────────
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


def S():
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20,
            textColor=BLUE_DARK, spaceAfter=2),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10,
            textColor=GRAY_DARK, spaceAfter=0),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11,
            textColor=BLUE_MID, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9,
            textColor=GRAY_DARK, leading=14, spaceAfter=4),
        "body_bold": ParagraphStyle("body_bold", fontName="Helvetica-Bold", fontSize=9,
            textColor=GRAY_DARK, leading=14),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#718096"), leading=12),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.HexColor("#a0aec0"), spaceAfter=2),
        "disclaimer": ParagraphStyle("disclaimer", fontName="Helvetica-Oblique", fontSize=8,
            textColor=colors.HexColor("#744210"), leading=12),
        "warning": ParagraphStyle("warning", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#744210"), leading=12),
        "emergency": ParagraphStyle("emergency", fontName="Helvetica-Bold", fontSize=10,
            textColor=WHITE, leading=14),
        "red_bold": ParagraphStyle("red_bold", fontName="Helvetica-Bold", fontSize=9,
            textColor=RED_DARK, leading=13),
        "green_bold": ParagraphStyle("green_bold", fontName="Helvetica-Bold", fontSize=9,
            textColor=GREEN_DARK, leading=13),
    }


def sev_color(level):
    if level == "Mild":
        return GREEN_DARK, GREEN_LIGHT
    elif level == "Moderate":
        return AMBER, AMBER_LIGHT
    elif level.startswith("Severe"):
        return RED_DARK, RED_LIGHT
    return GRAY_DARK, GRAY_LIGHT


def generate_pdf(report_data: dict) -> bytes:
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm,  bottomMargin=18*mm
    )

    styles  = S()
    story   = []
    W       = A4[0] - 36*mm
    now     = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # ── HEADER ───────────────────────────────────────────────────────────
    hdr = Table([[
        Paragraph("MediPredict — Drug Recommendation System", styles["title"]),
        Paragraph(f"Generated: {now}", ParagraphStyle("ts", fontName="Helvetica",
            fontSize=8, textColor=GRAY_DARK, alignment=TA_RIGHT))
    ]], colWidths=[W*0.65, W*0.35])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(hdr)
    story.append(Paragraph("Symptom-based disease diagnosis and safe drug recommendation", styles["subtitle"]))
    story.append(HRFlowable(width=W, thickness=1.5, color=BLUE_MID, spaceAfter=10))

    # ── PATIENT PROFILE ──────────────────────────────────────────────────
    profile          = report_data.get("profile", {})
    age_group        = profile.get("age_group", "adult").capitalize()
    gender           = profile.get("gender", "unspecified").capitalize()
    allergy          = profile.get("allergy", "none").capitalize()
    has_kidney       = "Yes" if profile.get("has_kidney_disease") else "No"
    is_pregnant      = "Yes" if profile.get("is_pregnant") else "No"
    symptoms         = report_data.get("symptoms", [])

    profile_rows = [
        [Paragraph("AGE GROUP", styles["label"]),
         Paragraph("GENDER", styles["label"]),
         Paragraph("ALLERGY", styles["label"]),
         Paragraph("KIDNEY DISEASE", styles["label"]),
         Paragraph("PREGNANT", styles["label"])],
        [Paragraph(age_group, styles["body_bold"]),
         Paragraph(gender, styles["body_bold"]),
         Paragraph(allergy, styles["body_bold"]),
         Paragraph(has_kidney, styles["body_bold"]),
         Paragraph(is_pregnant, styles["body_bold"])],
    ]
    pt = Table(profile_rows, colWidths=[W*0.15, W*0.15, W*0.15, W*0.25, W*0.3])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRAY_LIGHT),
        ("GRID", (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(pt)

    # Symptoms row
    story.append(Spacer(1, 6))
    sym_rows = [
        [Paragraph("SYMPTOMS ENTERED", styles["label"])],
        [Paragraph(
            ", ".join([s.replace("_", " ") for s in symptoms]) or "—",
            styles["body"]
        )],
    ]
    st = Table(sym_rows, colWidths=[W])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRAY_LIGHT),
        ("GRID", (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(st)
    story.append(Spacer(1, 8))

    # ── VITALS NOTES ─────────────────────────────────────────────────────
    vitals_notes = report_data.get("vitals_notes", [])
    if vitals_notes:
        story.append(Paragraph("Vital Signs Assessment", styles["section"]))
        for note in vitals_notes:
            story.append(Paragraph(f"• {note}", styles["body"]))
        story.append(Spacer(1, 6))

    # ── EMERGENCY BANNER ─────────────────────────────────────────────────
    if report_data.get("emergency"):
        reason = report_data.get("emergency_reason", "Please seek immediate medical attention.")
        em_data = [[Paragraph(f"EMERGENCY WARNING: {reason}", styles["emergency"])]]
        em_table = Table(em_data, colWidths=[W])
        em_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), RED_DARK),
            ("TOPPADDING", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING", (0,0), (-1,-1), 12),
        ]))
        story.append(em_table)
        story.append(Spacer(1, 10))

    # ── CLINICAL SUMMARY ─────────────────────────────────────────────────
    clinical_summary = report_data.get("clinical_summary")
    if clinical_summary:
        story.append(Paragraph("Patient History Summary", styles["section"]))
        story.append(Paragraph(clinical_summary, styles["body"]))
        story.append(Spacer(1, 6))

    # ── DIAGNOSIS ────────────────────────────────────────────────────────
    story.append(Paragraph("Diagnosis", styles["section"]))
    disease    = report_data.get("disease", "—")
    confidence = report_data.get("confidence", "—")
    conf_warn  = report_data.get("confidence_warning")

    diag_rows = [
        [Paragraph("PREDICTED DISEASE", styles["label"]),
         Paragraph("CONFIDENCE", styles["label"])],
        [Paragraph(disease, ParagraphStyle("dn", fontName="Helvetica-Bold",
             fontSize=14, textColor=BLUE_DARK)),
         Paragraph(confidence, ParagraphStyle("cn", fontName="Helvetica-Bold",
             fontSize=14, textColor=BLUE_MID))],
    ]
    dt = Table(diag_rows, colWidths=[W*0.7, W*0.3])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLUE_LIGHT),
        ("GRID", (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(dt)
    if conf_warn:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Note: {conf_warn}", styles["warning"]))

    # ── DIFFERENTIAL DIAGNOSES ───────────────────────────────────────────
    top3 = report_data.get("top3", [])
    if len(top3) > 1:
        story.append(Paragraph("Differential Diagnoses", styles["section"]))
        labels = ["Most likely", "2nd possibility", "3rd possibility"]
        diff_rows = [
            [Paragraph("RANK", styles["label"]),
             Paragraph("CONDITION", styles["label"]),
             Paragraph("CONFIDENCE", styles["label"])]
        ] + [
            [Paragraph(labels[i], styles["small"]),
             Paragraph(item["disease"], styles["body_bold"] if i == 0 else styles["body"]),
             Paragraph(item["confidence"], styles["body_bold"] if i == 0 else styles["body"])]
            for i, item in enumerate(top3)
        ]
        dt2 = Table(diff_rows, colWidths=[W*0.25, W*0.5, W*0.25])
        dt2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), GRAY_LIGHT),
            ("BACKGROUND", (0,1), (-1,1), BLUE_LIGHT),
            ("GRID", (0,0), (-1,-1), 0.5, BORDER),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(dt2)

    # ── SEVERITY ─────────────────────────────────────────────────────────
    severity = report_data.get("severity", {})
    s_level  = severity.get("level", "Unknown")
    s_score  = severity.get("score", 0)
    s_count  = severity.get("symptoms_matched", 0)
    s_fg, s_bg = sev_color(s_level)

    story.append(Paragraph("Severity Assessment", styles["section"]))
    sev_rows = [
        [Paragraph("LEVEL", styles["label"]),
         Paragraph("SCORE", styles["label"]),
         Paragraph("SYMPTOMS MATCHED", styles["label"])],
        [Paragraph(s_level, ParagraphStyle("sl", fontName="Helvetica-Bold",
             fontSize=11, textColor=s_fg)),
         Paragraph(str(s_score), styles["body_bold"]),
         Paragraph(str(s_count), styles["body_bold"])],
    ]
    st2 = Table(sev_rows, colWidths=[W*0.4, W*0.2, W*0.4])
    st2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), s_bg),
        ("GRID", (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(st2)

    # ── DESCRIPTION ──────────────────────────────────────────────────────
    description = report_data.get("description", "")
    if description:
        story.append(Paragraph("About This Disease", styles["section"]))
        story.append(Paragraph(description, styles["body"]))

    # ── PRECAUTIONS ──────────────────────────────────────────────────────
    precautions = report_data.get("precautions", [])
    if precautions:
        story.append(Paragraph("Recommended Precautions", styles["section"]))
        for i, p in enumerate(precautions, 1):
            story.append(Paragraph(f"{i}.  {p.capitalize()}", styles["body"]))

    # ── TREATMENT REGIMEN ────────────────────────────────────────────────
    medication = report_data.get("medication", {})
    regimen    = medication.get("regimen", [])
    reg_note   = medication.get("note", "")
    iw         = medication.get("interaction_warning")
    rn         = medication.get("regimen_notes")
    prof_notes = medication.get("profile_notes", [])

    story.append(Paragraph("Treatment Regimen", styles["section"]))
    if reg_note:
        story.append(Paragraph(reg_note, styles["small"]))
        story.append(Spacer(1, 6))

    # Drug interaction warning
    if iw and str(iw).strip() not in ["None", ""]:
        iw_data = [[Paragraph(f"Drug Interaction Notice: {iw}", styles["red_bold"])]]
        iw_table = Table(iw_data, colWidths=[W])
        iw_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), RED_LIGHT),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#fc8181")),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
        ]))
        story.append(iw_table)
        story.append(Spacer(1, 6))

    if not regimen:
        story.append(Paragraph("No safe medication found. Please consult a doctor.", styles["body"]))
    else:
        drug_header = [
            Paragraph("ROLE", styles["label"]),
            Paragraph("MEDICATION", styles["label"]),
            Paragraph("HOW TO TAKE", styles["label"]),
            Paragraph("FOR HOW LONG", styles["label"]),
        ]
        drug_rows = [drug_header]
        for drug in regimen:
            drug_rows.append([
                Paragraph(drug.get("role", ""), styles["small"]),
                Paragraph(drug.get("drug", ""), styles["body_bold"]),
                Paragraph(drug.get("dosage", ""), styles["body"]),
                Paragraph(drug.get("duration", ""), styles["body"]),
            ])
        drug_table = Table(drug_rows,
            colWidths=[W*0.20, W*0.20, W*0.38, W*0.22], repeatRows=1)
        drug_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), GRAY_LIGHT),
            ("BACKGROUND", (0,1), (-1,1), BLUE_LIGHT),
            ("ROWBACKGROUNDS", (0,2), (-1,-1), [WHITE, GRAY_LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.5, BORDER),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(drug_table)

    # Regimen notes
    if rn and str(rn).strip() not in ["None", ""]:
        story.append(Spacer(1, 6))
        rn_data = [[Paragraph(f"Important Instructions: {rn}", styles["green_bold"])]]
        rn_table = Table(rn_data, colWidths=[W])
        rn_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), GREEN_LIGHT),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#68d391")),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
        ]))
        story.append(rn_table)

    # Profile advisory notes
    if prof_notes:
        story.append(Paragraph("Patient Profile Advisories", styles["section"]))
        for note in prof_notes:
            note_data = [[Paragraph(note, styles["warning"])]]
            note_table = Table(note_data, colWidths=[W])
            note_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), AMBER_LIGHT),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#f6ad55")),
                ("TOPPADDING", (0,0), (-1,-1), 8),
                ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                ("LEFTPADDING", (0,0), (-1,-1), 10),
            ]))
            story.append(note_table)
            story.append(Spacer(1, 4))

    # ── DISCLAIMER ───────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER, spaceAfter=8))
    story.append(Paragraph(
        "Medical Disclaimer: This report is generated by a computer-based system for "
        "informational purposes only. It does not constitute professional medical advice, "
        "diagnosis, or treatment. Always consult a qualified healthcare provider before "
        "starting, stopping, or changing any medication. Dosages listed are standard "
        "reference values and may need adjustment based on individual patient factors "
        "including weight, kidney function, and other medical conditions.",
        styles["disclaimer"]
    ))

    doc.build(story)
    return buffer.getvalue()