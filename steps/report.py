import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_pdf_report(image_name, defects):
    """Build a styled PDF inspection report and return it as bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    # styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#333333"),
        leading=14,
    )
    verdict_style = ParagraphStyle(
        "Verdict",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
    )

    SEV_COLOR = {
        "High":   colors.HexColor("#ff4444"),
        "Medium": colors.HexColor("#fa8c16"),
        "Low":    colors.HexColor("#389e0d"),
    }

    story = []

    # header
    story.append(Paragraph("INSPECTION REPORT", title_style))
    story.append(Paragraph(
        f"Image: <b>{image_name}</b> &nbsp;|&nbsp; "
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"Total Defects: <b>{len(defects)}</b>",
        sub_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a1a2e"), spaceAfter=8))

    # no defects
    if not defects:
        story.append(Paragraph(
            "<font color='#389e0d'><b>PASS</b></font> — No defects detected. Component looks good.",
            body_style,
        ))
        doc.build(story)
        return buf.getvalue()

    # defect summary table
    story.append(Paragraph("Defect Summary", section_style))

    table_data = [[
        Paragraph("<b>#</b>", body_style),
        Paragraph("<b>Type</b>", body_style),
        Paragraph("<b>Severity</b>", body_style),
        Paragraph("<b>Score</b>", body_style),
        Paragraph("<b>Location</b>", body_style),
        Paragraph("<b>Confidence</b>", body_style),
        Paragraph("<b>Coverage</b>", body_style),
    ]]

    row_fills = []
    for i, d in enumerate(defects, 1):
        sev = d["severity_level"]
        sev_para = Paragraph(
            f"<font color='{SEV_COLOR.get(sev, colors.black).hexval() if hasattr(SEV_COLOR.get(sev, colors.black), 'hexval') else '#000000'}'><b>{sev}</b></font>",
            body_style,
        )
    
        sev_text = Paragraph(f"<b>{sev}</b>", ParagraphStyle(
            f"sev_{i}",
            parent=body_style,
            textColor=SEV_COLOR.get(sev, colors.black),
        ))
        table_data.append([
            Paragraph(str(i), body_style),
            Paragraph(d["type"], body_style),
            sev_text,
            Paragraph(f"{d['severity_score']}/100", body_style),
            Paragraph(d["location"], body_style),
            Paragraph(f"{int(d['confidence'] * 100)}%", body_style),
            Paragraph(f"{d['size_percent']}%", body_style),
        ])
        row_fills.append(i)  

    col_widths = [10 * mm, 40 * mm, 22 * mm, 20 * mm, 28 * mm, 24 * mm, 22 * mm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    tbl_style = [
        # header row
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f7f9fc"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    tbl.setStyle(TableStyle(tbl_style))
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # root cause analysis
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4))
    story.append(Paragraph("Root Cause Analysis", section_style))

    for d in defects:
        sev = d["severity_level"]
        sev_color = SEV_COLOR.get(sev, colors.black)
        story.append(Paragraph(
            f"<b>{d['type']}</b> &nbsp; "
            f"<font color='{sev_color.hexColor() if hasattr(sev_color, 'hexColor') else '#000000'}'>{sev} Severity</font>",
            ParagraphStyle("rca_head", parent=body_style, fontSize=10,
                           textColor=colors.HexColor("#1a1a2e"), spaceBefore=6),
        ))

        def bullet_list(label, items):
            if not items:
                return []
            out = [Paragraph(f"<b>{label}:</b>", body_style)]
            for item in items:
                out.append(Paragraph(f"&nbsp;&nbsp;• {item}", body_style))
            return out

        story += bullet_list("Causes",  d.get("causes", []))
        story += bullet_list("Risks",   d.get("risks", []))
        story += bullet_list("Actions", d.get("actions", []))
        story.append(Paragraph(
            f"<i>Source: {d.get('reasoning_source', 'N/A')}</i>",
            ParagraphStyle("src", parent=body_style, textColor=colors.HexColor("#888888")),
        ))
        story.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#dddddd"), spaceAfter=2))

    # overall verdict
    story.append(Spacer(1, 4 * mm))
    high_count = sum(1 for d in defects if d["severity_level"] == "High")
    if high_count > 0:
        verdict_text  = f"<font color='#ff4444'><b>FAIL</b></font> — {high_count} high-severity defect(s) detected. Immediate action required."
        verdict_bg    = colors.HexColor("#fff0f0")
        verdict_border = colors.HexColor("#ff4444")
    elif len(defects) > 3:
        verdict_text  = f"<font color='#fa8c16'><b>WARNING</b></font> — {len(defects)} defects detected. Schedule maintenance soon."
        verdict_bg    = colors.HexColor("#fff7e6")
        verdict_border = colors.HexColor("#fa8c16")
    else:
        verdict_text  = f"<font color='#389e0d'><b>PASS WITH NOTES</b></font> — {len(defects)} minor defect(s). Monitor in next cycle."
        verdict_bg    = colors.HexColor("#f0fff4")
        verdict_border = colors.HexColor("#389e0d")

    verdict_para = Paragraph(verdict_text, verdict_style)
    verdict_tbl  = Table([[verdict_para]], colWidths=[doc.width])
    verdict_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), verdict_bg),
        ("BOX",         (0, 0), (-1, -1), 1.5, verdict_border),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(verdict_tbl)

    doc.build(story)
    return buf.getvalue()


def generate_report(image_name, defects):
    """Build a formatted text report from the defect data."""
    lines = []
    lines.append("=" * 50)
    lines.append("       INSPECTION REPORT")
    lines.append("=" * 50)
    lines.append(f"Image: {image_name}")
    lines.append(f"Total Defects Found: {len(defects)}")
    lines.append("-" * 50)

    if not defects:
        lines.append("No defects detected. Component PASSES inspection.")
        return "\n".join(lines)

    # summary table
    lines.append("\nDEFECT SUMMARY:")
    lines.append("-" * 75)

    for i, d in enumerate(defects, 1):
        lines.append(f"  Defect #{i}")
        lines.append(f"    Type:           {d['type']}")
        lines.append(f"    Severity:       {d['severity_level']}  (Score: {d['severity_score']}/100)")
        lines.append(f"    Location:       {d['location']}")
        lines.append(f"    Confidence:     {d['confidence']}")
        lines.append(f"    Surface Cover:  {d['size_percent']}%")
        lines.append("-" * 75)

    # root cause section
    lines.append("\n\nROOT CAUSE ANALYSIS:")
    lines.append("-" * 50)

    for d in defects:
        lines.append(f"\n> {d['type']} ({d['severity_level']} Severity)")
        lines.append("  Causes:")
        for c in d.get("causes", []):
            lines.append(f"    - {c}")
        lines.append("  Risks:")
        for r in d.get("risks", []):
            lines.append(f"    - {r}")
        lines.append("  Actions:")
        for a in d.get("actions", []):
            lines.append(f"    - {a}")
        lines.append(f"  (Source: {d.get('reasoning_source', 'N/A')})")

    # final verdict
    high_count = sum(1 for d in defects if d["severity_level"] == "High")
    if high_count > 0:
        verdict = "FAIL - High severity defects found. Immediate action needed."
    elif len(defects) > 3:
        verdict = "WARNING - Multiple defects detected. Schedule maintenance."
    else:
        verdict = "PASS with NOTES - Minor defects. Monitor in next cycle."

    lines.append(f"\n\nOVERALL: {verdict}")
    lines.append("=" * 50)

    return "\n".join(lines)
