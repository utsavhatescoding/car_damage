from __future__ import annotations

import io
import json
from datetime import datetime, timezone

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .model_service import Detection


NAVY = colors.HexColor("#07192E")
BLUE = colors.HexColor("#2F7CF6")
RED = colors.HexColor("#F04455")
INK = colors.HexColor("#102033")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#DCE5EF")
PAPER = colors.HexColor("#F3F6FA")
GREEN = colors.HexColor("#1B9C6B")


def _image_buffer(image: Image.Image, max_size=(1600, 1600)) -> io.BytesIO:
    working = image.convert("RGB").copy()
    working.thumbnail(max_size)
    buffer = io.BytesIO()
    working.save(buffer, format="JPEG", quality=90, optimize=True)
    buffer.seek(0)
    return buffer


def build_json_report(payload: dict) -> bytes:
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def build_pdf_report(
    inspection: dict,
    quality: dict,
    detections: list[Detection],
    original_image: Image.Image,
    annotated_image: Image.Image,
) -> bytes:
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Gaadi Inspector Report {inspection['inspection_id']}",
        author="Gaadi Inspector",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="GIHero", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=colors.white, spaceAfter=5))
    styles.add(ParagraphStyle(name="GISub", parent=styles["Normal"], fontSize=9, leading=14, textColor=colors.HexColor("#C4D5E7")))
    styles.add(ParagraphStyle(name="GISection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="GIBody", parent=styles["BodyText"], fontSize=8.5, leading=13, textColor=INK))
    styles.add(ParagraphStyle(name="GISmall", parent=styles["BodyText"], fontSize=7.4, leading=11, textColor=MUTED))
    styles.add(ParagraphStyle(name="GIRight", parent=styles["GISmall"], alignment=TA_RIGHT))

    accepted = [item for item in detections if item.review_status == "Accepted"]
    review = [item for item in detections if item.review_status == "Needs review"]
    rejected = [item for item in detections if item.review_status == "Rejected"]

    header_left = [
        Paragraph("GAADI INSPECTOR", styles["GIHero"]),
        Paragraph("AI-assisted visible vehicle damage inspection", styles["GISub"]),
    ]
    header_right = [
        Paragraph("INSPECTION REPORT", ParagraphStyle("badge", parent=styles["GIRight"], textColor=colors.HexColor("#A8DDFF"), fontName="Helvetica-Bold")),
        Paragraph(inspection["inspection_id"], ParagraphStyle("id", parent=styles["GIRight"], textColor=colors.white, fontSize=10, fontName="Helvetica-Bold")),
    ]
    hero = Table([[header_left, header_right]], colWidths=[113 * mm, 48 * mm])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0, NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 14),
        ("RIGHTPADDING", (-1, 0), (-1, 0), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    story = [hero, Spacer(1, 5 * mm)]

    status = "REVIEW REQUIRED" if review else "REVIEW COMPLETE"
    status_colour = RED if review else GREEN
    summary_data = [
        [Paragraph("STATUS", styles["GISmall"]), Paragraph("DETECTED", styles["GISmall"]), Paragraph("ACCEPTED", styles["GISmall"]), Paragraph("REJECTED", styles["GISmall"])],
        [Paragraph(f"<b><font color='{status_colour.hexval()}'>{status}</font></b>", styles["GIBody"]), Paragraph(f"<b>{len(detections)}</b>", styles["GIBody"]), Paragraph(f"<b>{len(accepted)}</b>", styles["GIBody"]), Paragraph(f"<b>{len(rejected)}</b>", styles["GIBody"])],
    ]
    summary = Table(summary_data, colWidths=[65 * mm, 32 * mm, 32 * mm, 32 * mm])
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), .7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), .5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([summary, Paragraph("Vehicle & inspection details", styles["GISection"])])

    detail_pairs = [
        ("Reg. number", inspection.get("registration") or "Not provided"),
        ("Vehicle", " ".join(filter(None, [inspection.get("year"), inspection.get("make"), inspection.get("model")])) or "Not provided"),
        ("Inspector", inspection.get("inspector") or "Not provided"),
        ("Purpose", inspection.get("purpose") or "General visible-damage check"),
        ("Captured", inspection.get("created_at_display", "")),
        ("Source", inspection.get("source", "Uploaded photo")),
    ]
    detail_rows = []
    for index in range(0, len(detail_pairs), 2):
        row = []
        for label, value in detail_pairs[index:index + 2]:
            row.extend([Paragraph(label.upper(), styles["GISmall"]), Paragraph(str(value), styles["GIBody"])])
        detail_rows.append(row)
    details = Table(detail_rows, colWidths=[24 * mm, 56.5 * mm, 24 * mm, 56.5 * mm])
    details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), .6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), .4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([details, Paragraph("Inspection evidence", styles["GISection"])])

    original_buffer = _image_buffer(original_image)
    annotated_buffer = _image_buffer(annotated_image)
    original_rl = RLImage(original_buffer)
    annotated_rl = RLImage(annotated_buffer)
    for report_image in (original_rl, annotated_rl):
        ratio = report_image.imageHeight / report_image.imageWidth
        report_image.drawWidth = 78.5 * mm
        report_image.drawHeight = min(49 * mm, 78.5 * mm * ratio)

    evidence = Table([
        [Paragraph("ORIGINAL", styles["GISmall"]), Paragraph("AI-ANNOTATED", styles["GISmall"])],
        [original_rl, annotated_rl],
    ], colWidths=[80.5 * mm, 80.5 * mm])
    evidence.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), .6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), .4, BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), PAPER),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]))
    story.append(evidence)

    story.append(Paragraph("Detection review", styles["GISection"]))
    table_data = [["ID", "Damage", "Confidence", "Review", "Inspector note"]]
    for item in detections:
        table_data.append([
            item.detection_id,
            item.damage_type.title(),
            f"{item.confidence:.1%}",
            item.review_status,
            Paragraph(item.note or "-", styles["GISmall"]),
        ])
    if len(table_data) == 1:
        table_data.append(["-", "No supported damage detected", "-", "Review image", "No detections above the selected threshold."])

    detection_table = Table(table_data, repeatRows=1, colWidths=[14 * mm, 35 * mm, 23 * mm, 30 * mm, 59 * mm])
    detection_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER]),
        ("BOX", (0, 0), (-1, -1), .6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), .35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]))
    story.append(detection_table)

    story.extend([
        Paragraph("Image quality record", styles["GISection"]),
        Paragraph(
            f"Resolution: {quality['width']} x {quality['height']} ({quality['megapixels']} MP) &nbsp;&nbsp;-&nbsp;&nbsp; "
            f"Brightness: {quality['brightness_status']} &nbsp;&nbsp;-&nbsp;&nbsp; Sharpness: {quality['sharpness_status']}",
            styles["GIBody"],
        ),
        Spacer(1, 3 * mm),
        Table([["", ""]], colWidths=[80.5 * mm, 80.5 * mm], rowHeights=[1.5 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), BLUE),
            ("BACKGROUND", (1, 0), (1, 0), RED),
        ])),
        Spacer(1, 4 * mm),
        Paragraph(
            "IMPORTANT - This report is an AI-assisted preliminary assessment of visible exterior damage in the supplied image. "
            "It does not assess mechanical, structural, underbody or internal condition. A qualified human inspector must verify "
            "all detections and inspect the vehicle before insurance, purchase, safety or repair decisions.",
            styles["GISmall"],
        ),
    ])

    def page_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(17 * mm, 12 * mm, 193 * mm, 12 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(17 * mm, 7.5 * mm, f"Gaadi Inspector - {inspection['inspection_id']} - Independent AI-assisted inspection support")
        canvas.drawRightString(193 * mm, 7.5 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return output.getvalue()


def report_payload(inspection: dict, quality: dict, detections: list[Detection], inference_ms: float) -> dict:
    return {
        "schema_version": "1.0",
        "product": "Gaadi Inspector",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inspection": inspection,
        "image_quality": quality,
        "inference_ms": inference_ms,
        "detections": [item.to_dict() for item in detections],
        "disclaimer": "AI-assisted visible exterior assessment. Human verification required.",
    }
