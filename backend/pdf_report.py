from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime

# ── COLOUR PALETTE ───────────────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#1a4a7a")
BLUE_MID    = colors.HexColor("#2b6cb0")
BLUE_LIGHT  = colors.HexColor("#dbeafe")
BLUE_PALE   = colors.HexColor("#f0f7ff")
AMBER       = colors.HexColor("#b45309")
AMBER_LIGHT = colors.HexColor("#fffbeb")
AMBER_BORD  = colors.HexColor("#f6ad55")
RED_DARK    = colors.HexColor("#991b1b")
RED_MID     = colors.HexColor("#dc2626")
RED_LIGHT   = colors.HexColor("#fef2f2")
RED_BORD    = colors.HexColor("#fca5a5")
GREEN_DARK  = colors.HexColor("#166534")
GREEN_MID   = colors.HexColor("#16a34a")
GREEN_LIGHT = colors.HexColor("#f0fdf4")
GREEN_BORD  = colors.HexColor("#86efac")
GRAY_DARK   = colors.HexColor("#374151")
GRAY_MED    = colors.HexColor("#6b7280")
GRAY_LIGHT  = colors.HexColor("#f9fafb")
GRAY_BORD   = colors.HexColor("#e5e7eb")
WHITE       = colors.white
BLACK       = colors.HexColor("#111827")

W = A4[0] - 32*mm   # usable page width


def make_styles():
    return {
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold",
            fontSize=18, textColor=BLUE_DARK, leading=22, spaceAfter=2),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold",
            fontSize=11, textColor=BLUE_MID,
            spaceBefore=12, spaceAfter=5),
        "meta": ParagraphStyle("meta", fontName="Helvetica",
            fontSize=9, textColor=GRAY_MED),
        "meta_right": ParagraphStyle("meta_right", fontName="Helvetica",
            fontSize=9, textColor=GRAY_MED, alignment=TA_RIGHT),
        "body": ParagraphStyle("body", fontName="Helvetica",
            fontSize=9, textColor=GRAY_DARK, leading=13),
        "body_bold": ParagraphStyle("body_bold", fontName="Helvetica-Bold",
            fontSize=9, textColor=BLACK, leading=13),
        "small": ParagraphStyle("small", fontName="Helvetica",
            fontSize=8, textColor=GRAY_MED, leading=11),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold",
            fontSize=7, textColor=GRAY_MED,
            spaceAfter=2, leading=10),
        "drug_name": ParagraphStyle("drug_name", fontName="Helvetica-Bold",
            fontSize=9, textColor=BLUE_DARK, leading=12),
        "em_text": ParagraphStyle("em_text", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE, leading=13),
        "warn_text": ParagraphStyle("warn_text", fontName="Helvetica",
            fontSize=8, textColor=AMBER, leading=12),
        "red_text": ParagraphStyle("red_text", fontName="Helvetica-Bold",
            fontSize=8, textColor=RED_MID, leading=12),
        "green_text": ParagraphStyle("green_text", fontName="Helvetica",
            fontSize=8, textColor=GREEN_DARK, leading=12),
        "disclaimer": ParagraphStyle("disclaimer", fontName="Helvetica-Oblique",
            fontSize=7.5, textColor=GRAY_MED, leading=11),
    }


def sev_colors(level):
    if level == "Mild":
        return GREEN_DARK, GREEN_LIGHT, GREEN_BORD
    elif level == "Moderate":
        return AMBER, AMBER_LIGHT, AMBER_BORD
    elif level.startswith("Severe"):
        return RED_MID, RED_LIGHT, RED_BORD
    return GRAY_MED, GRAY_LIGHT, GRAY_BORD


def box_table(content_rows, bg, border, col_widths=None):
    """Utility: wrap rows in a styled table box."""
    t = Table(content_rows, colWidths=col_widths or [W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX",        (0, 0), (-1, -1), 0.75, border),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    return t


def generate_pdf(report_data: dict) -> bytes:
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=16*mm, rightMargin=16*mm,
        topMargin=14*mm,  bottomMargin=14*mm
    )

    S     = make_styles()
    story = []
    now   = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # ════════════════════════════════════════════════════════════════════
    # HEADER BLOCK
    # ════════════════════════════════════════════════════════════════════
    story.append(Table(
        [[
            Paragraph("MediPredict", S["h1"]),
            Paragraph(f"Generated: {now}", S["meta_right"])
        ]],
        colWidths=[W * 0.6, W * 0.4]
    ))
    story.append(Paragraph(
        "Drug Recommendation System — Symptom-based disease diagnosis",
        S["meta"]
    ))
    story.append(HRFlowable(
        width=W, thickness=2, color=BLUE_MID,
        spaceBefore=6, spaceAfter=10
    ))

    # ════════════════════════════════════════════════════════════════════
    # PATIENT PROFILE
    # ════════════════════════════════════════════════════════════════════
    profile     = report_data.get("profile", {})
    age_group   = profile.get("age_group", "adult").capitalize()
    gender      = profile.get("gender", "unspecified").capitalize()
    allergy     = profile.get("allergy", "none").capitalize()
    has_kidney  = "Yes" if profile.get("has_kidney_disease") else "No"
    is_pregnant = "Yes" if profile.get("is_pregnant") else "No"
    symptoms    = report_data.get("symptoms", [])

    story.append(Paragraph("Patient Profile", S["h2"]))

    profile_header = [
        Paragraph("AGE GROUP", S["label"]),
        Paragraph("GENDER",    S["label"]),
        Paragraph("ALLERGY",   S["label"]),
        Paragraph("KIDNEY DISEASE", S["label"]),
        Paragraph("PREGNANT",  S["label"]),
    ]
    profile_values = [
        Paragraph(age_group,   S["body_bold"]),
        Paragraph(gender,      S["body_bold"]),
        Paragraph(allergy,     S["body_bold"]),
        Paragraph(has_kidney,  S["body_bold"]),
        Paragraph(is_pregnant, S["body_bold"]),
    ]
    cw5 = [W/5] * 5
    pt = Table([profile_header, profile_values], colWidths=cw5)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE_DARK),
        ("BACKGROUND", (0,1), (-1,1), BLUE_PALE),
        ("TEXTCOLOR",  (0,0), (-1,0), WHITE),
        ("BOX",   (0,0), (-1,-1), 0.5, BLUE_MID),
        ("GRID",  (0,0), (-1,-1), 0.3, GRAY_BORD),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 4))

    # Symptoms row
    sym_text = ", ".join([s.replace("_", " ") for s in symptoms]) or "None entered"
    sym_table = Table(
        [[Paragraph("SYMPTOMS ENTERED", S["label"])],
         [Paragraph(sym_text, S["body"])]],
        colWidths=[W]
    )
    sym_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE_DARK),
        ("BACKGROUND", (0,1), (-1,1), BLUE_PALE),
        ("TEXTCOLOR",  (0,0), (-1,0), WHITE),
        ("BOX",  (0,0), (-1,-1), 0.5, BLUE_MID),
        ("GRID", (0,0), (-1,-1), 0.3, GRAY_BORD),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(sym_table)
    story.append(Spacer(1, 8))

    # ════════════════════════════════════════════════════════════════════
    # VITAL SIGNS
    # ════════════════════════════════════════════════════════════════════
    vitals_notes = report_data.get("vitals_notes", [])
    if vitals_notes:
        story.append(Paragraph("Vital Signs Assessment", S["h2"]))
        rows = [[Paragraph(f"• {n}", S["body"])] for n in vitals_notes]
        story.append(box_table(rows, GREEN_LIGHT, GREEN_BORD))
        story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════════════════
    # EMERGENCY BANNER
    # ════════════════════════════════════════════════════════════════════
    if report_data.get("emergency"):
        reason = report_data.get("emergency_reason", "Please seek immediate medical attention.")
        em = Table(
            [[Paragraph(f"⚠  EMERGENCY WARNING", S["em_text"])],
             [Paragraph(reason, S["em_text"])]],
            colWidths=[W]
        )
        em.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), RED_MID),
            ("BOX", (0,0), (-1,-1), 1, RED_DARK),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ]))
        story.append(em)
        story.append(Spacer(1, 8))

    # ════════════════════════════════════════════════════════════════════
    # CLINICAL SUMMARY
    # ════════════════════════════════════════════════════════════════════
    clinical_summary = report_data.get("clinical_summary")
    if clinical_summary:
        story.append(Paragraph("Patient History Summary", S["h2"]))
        story.append(box_table(
            [[Paragraph(clinical_summary, S["body"])]],
            GREEN_LIGHT, GREEN_BORD
        ))
        story.append(Spacer(1, 8))

    # ════════════════════════════════════════════════════════════════════
    # DIAGNOSIS
    # ════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Diagnosis", S["h2"]))
    disease    = report_data.get("disease", "—")
    confidence = report_data.get("confidence", "—")
    conf_warn  = report_data.get("confidence_warning")

    diag = Table(
        [[Paragraph("PREDICTED DISEASE", S["label"]),
          Paragraph("CONFIDENCE", S["label"])],
         [Paragraph(disease, ParagraphStyle("dn", fontName="Helvetica-Bold",
              fontSize=15, textColor=WHITE)),
          Paragraph(confidence, ParagraphStyle("cn", fontName="Helvetica-Bold",
              fontSize=15, textColor=WHITE))]],
        colWidths=[W * 0.7, W * 0.3]
    )
    diag.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLUE_DARK),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.HexColor("#93c5fd")),
        ("BOX",  (0,0), (-1,-1), 0.5, BLUE_MID),
        ("GRID", (0,0), (-1,-1), 0.3, BLUE_MID),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(diag)

    if conf_warn:
        story.append(Spacer(1, 4))
        story.append(box_table(
            [[Paragraph(f"Confidence Note: {conf_warn}", S["warn_text"])]],
            AMBER_LIGHT, AMBER_BORD
        ))
    story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════════════════
    # DIFFERENTIAL DIAGNOSES
    # ════════════════════════════════════════════════════════════════════
    top3 = report_data.get("top3", [])
    if len(top3) > 1:
        story.append(Paragraph("Differential Diagnoses", S["h2"]))
        labels = ["Most likely", "2nd possibility", "3rd possibility"]
        diff_header = [
            Paragraph("RANK",       S["label"]),
            Paragraph("CONDITION",  S["label"]),
            Paragraph("CONFIDENCE", S["label"]),
        ]
        diff_rows = [diff_header]
        for i, item in enumerate(top3):
            bold = i == 0
            diff_rows.append([
                Paragraph(labels[i], S["body_bold"] if bold else S["body"]),
                Paragraph(item["disease"], S["body_bold"] if bold else S["body"]),
                Paragraph(item["confidence"], S["body_bold"] if bold else S["body"]),
            ])
        dt = Table(diff_rows, colWidths=[W*0.25, W*0.5, W*0.25])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), BLUE_DARK),
            ("TEXTCOLOR",  (0,0), (-1,0), WHITE),
            ("BACKGROUND", (0,1), (-1,1), BLUE_LIGHT),
            ("ROWBACKGROUNDS", (0,2), (-1,-1), [WHITE, BLUE_PALE]),
            ("BOX",  (0,0), (-1,-1), 0.5, BLUE_MID),
            ("GRID", (0,0), (-1,-1), 0.3, GRAY_BORD),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(dt)
        story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════════════════
    # SEVERITY
    # ════════════════════════════════════════════════════════════════════
    severity = report_data.get("severity", {})
    s_level  = severity.get("level", "Unknown")
    s_score  = severity.get("score", 0)
    s_count  = severity.get("symptoms_matched", 0)
    s_fg, s_bg, s_bord = sev_colors(s_level)

    story.append(Paragraph("Severity Assessment", S["h2"]))
    sev_header = [
        Paragraph("SEVERITY LEVEL",    S["label"]),
        Paragraph("SCORE",             S["label"]),
        Paragraph("SYMPTOMS MATCHED",  S["label"]),
    ]
    sev_values = [
        Paragraph(s_level, ParagraphStyle("sl", fontName="Helvetica-Bold",
            fontSize=9, textColor=s_fg)),
        Paragraph(str(s_score), S["body_bold"]),
        Paragraph(str(s_count), S["body_bold"]),
    ]
    st = Table([sev_header, sev_values], colWidths=[W*0.5, W*0.2, W*0.3])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRAY_LIGHT),
        ("BACKGROUND", (0,1), (-1,1), s_bg),
        ("BOX",  (0,0), (-1,-1), 0.75, s_bord),
        ("GRID", (0,0), (-1,-1), 0.3, GRAY_BORD),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(st)
    story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════════════════
    # DESCRIPTION
    # ════════════════════════════════════════════════════════════════════
    description = report_data.get("description", "")
    if description:
        story.append(Paragraph("About This Disease", S["h2"]))
        story.append(Paragraph(description, S["body"]))
        story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════════════════
    # PRECAUTIONS
    # ════════════════════════════════════════════════════════════════════
    precautions = report_data.get("precautions", [])
    if precautions:
        story.append(Paragraph("Recommended Precautions", S["h2"]))
        rows = [[Paragraph(f"{i+1}.  {p.strip().capitalize()}", S["body"])]
                for i, p in enumerate(precautions)]
        story.append(box_table(rows, BLUE_PALE, BLUE_MID))
        story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════════════════
    # TREATMENT REGIMEN
    # ════════════════════════════════════════════════════════════════════
    medication = report_data.get("medication", {})
    regimen    = medication.get("regimen", [])
    reg_note   = medication.get("note", "")
    iw         = medication.get("interaction_warning")
    rn         = medication.get("regimen_notes")
    prof_notes = medication.get("profile_notes", [])

    story.append(Paragraph("Treatment Regimen", S["h2"]))

    if reg_note and str(reg_note).strip() not in ["", "None"]:
        story.append(Paragraph(reg_note, S["small"]))
        story.append(Spacer(1, 4))

    # Drug interaction warning
    if iw and str(iw).strip() not in ["", "None"]:
        story.append(box_table(
            [[Paragraph(f"Drug Interaction Notice: {iw}", S["red_text"])]],
            RED_LIGHT, RED_BORD
        ))
        story.append(Spacer(1, 4))

    if not regimen:
        story.append(Paragraph(
            "No safe medication found for your profile. Please consult a doctor.",
            S["body"]
        ))
    else:
        # Drug table with generous column widths
        drug_header = [
            Paragraph("ROLE",         S["label"]),
            Paragraph("MEDICATION",   S["label"]),
            Paragraph("HOW TO TAKE",  S["label"]),
            Paragraph("FOR HOW LONG", S["label"]),
        ]
        drug_rows = [drug_header]
        for drug in regimen:
            drug_rows.append([
                Paragraph(drug.get("role", ""),     S["small"]),
                Paragraph(drug.get("drug", ""),     S["drug_name"]),
                Paragraph(drug.get("dosage", ""),   S["body"]),
                Paragraph(drug.get("duration", ""), S["body"]),
            ])

        # Column widths: role narrow, drug name wider, dosage widest, duration medium
        cw = [W*0.18, W*0.22, W*0.38, W*0.22]
        drug_table = Table(drug_rows, colWidths=cw, repeatRows=1)
        drug_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), BLUE_DARK),
            ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
            ("BACKGROUND",    (0,1), (-1,1), BLUE_LIGHT),
            ("ROWBACKGROUNDS",(0,2), (-1,-1), [WHITE, BLUE_PALE]),
            ("BOX",           (0,0), (-1,-1), 0.75, BLUE_MID),
            ("INNERGRID",     (0,0), (-1,-1), 0.3, GRAY_BORD),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 7),
            ("RIGHTPADDING",  (0,0), (-1,-1), 7),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("WORDWRAP",      (0,0), (-1,-1), True),
        ]))
        story.append(drug_table)

    # Regimen notes
    if rn and str(rn).strip() not in ["", "None"]:
        story.append(Spacer(1, 4))
        story.append(box_table(
            [[Paragraph(f"Important Instructions: {rn}", S["green_text"])]],
            GREEN_LIGHT, GREEN_BORD
        ))

    # Profile advisory notes
    if prof_notes:
        story.append(Spacer(1, 6))
        story.append(Paragraph("Patient Profile Advisories", S["h2"]))
        for note in prof_notes:
            story.append(box_table(
                [[Paragraph(note, S["warn_text"])]],
                AMBER_LIGHT, AMBER_BORD
            ))
            story.append(Spacer(1, 3))

    # ════════════════════════════════════════════════════════════════════
    # DISCLAIMER
    # ════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(HRFlowable(
        width=W, thickness=0.5, color=GRAY_BORD, spaceAfter=6
    ))
    story.append(Paragraph(
        "Medical Disclaimer: This report is generated by a computer-based system for "
        "informational purposes only. It does not constitute professional medical advice, "
        "diagnosis, or treatment. Always consult a qualified healthcare provider before "
        "starting, stopping, or changing any medication. Dosages listed are standard "
        "reference values and may need adjustment based on individual patient factors "
        "including weight, kidney function, and other medical conditions.",
        S["disclaimer"]
    ))

    doc.build(story)
    return buffer.getvalue()