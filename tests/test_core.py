from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageDraw

from src.image_quality import assess_image_quality
from src.live_service import draw_live_detections
from src.model_service import Detection, annotate_image
from src.report_service import build_pdf_report, report_payload


def sample_image() -> Image.Image:
    image = Image.new("RGB", (1000, 700), "#bcc8d6")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 150, 900, 560), fill="#35475b")
    draw.ellipse((430, 280, 590, 410), outline="#e8edf3", width=10)
    return image


def test_quality_and_annotation():
    image = sample_image()
    quality = assess_image_quality(image)
    assert quality.width == 1000
    assert quality.height == 700

    detection = Detection(
        detection_id="D-01",
        damage_type="dent",
        confidence=0.84,
        bbox={"x1": 420, "y1": 270, "x2": 600, "y2": 430},
        review_status="Accepted",
    )
    annotated = annotate_image(image, [detection])
    assert annotated.size == image.size


def test_pdf_generation():
    image = sample_image()
    quality = assess_image_quality(image)
    detection = Detection(
        detection_id="D-01",
        damage_type="dent",
        confidence=0.84,
        bbox={"x1": 420, "y1": 270, "x2": 600, "y2": 430},
        review_status="Accepted",
        note="Visible shallow dent on panel.",
    )
    annotated = annotate_image(image, [detection])
    inspection = {
        "inspection_id": "GI-TEST-0001",
        "registration": "BA 01 PA 1234",
        "make": "Toyota",
        "model": "Corolla",
        "year": "2020",
        "inspector": "Test Inspector",
        "purpose": "Used-vehicle assessment",
        "created_at_display": "30 Aug 2026, 10:00 AM",
        "source": "Uploaded photo",
    }
    pdf = build_pdf_report(inspection, quality.to_dict(), [detection], image, annotated)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 10_000


def test_live_overlay():
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    result = draw_live_detections(
        frame,
        [
            {
                "damage_type": "scratch",
                "confidence": 0.72,
                "bbox": [220, 180, 620, 410],
            }
        ],
    )
    assert result.shape == frame.shape
    assert np.any(result != frame)
