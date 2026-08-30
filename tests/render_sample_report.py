"""Generate a representative report for visual quality assurance."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw

from src.image_quality import assess_image_quality
from src.model_service import Detection, annotate_image
from src.report_service import build_pdf_report


def build_sample_image() -> Image.Image:
    image = Image.new("RGB", (1400, 900), "#D7E1EB")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((110, 175, 1290, 740), radius=100, fill="#596C81")
    draw.polygon([(320, 225), (1080, 225), (1190, 445), (205, 445)], fill="#9EB2C5")
    draw.ellipse((480, 330, 770, 575), outline="#E9F0F7", width=18)
    draw.line((545, 395, 705, 505), fill="#F7C3C8", width=15)
    draw.ellipse((205, 615, 405, 815), fill="#18283A")
    draw.ellipse((995, 615, 1195, 815), fill="#18283A")
    return image


def main() -> None:
    output_dir = Path("output/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    image = build_sample_image()
    detections = [
        Detection(
            detection_id="D-01",
            damage_type="dent",
            confidence=0.86,
            bbox={"x1": 475, "y1": 325, "x2": 775, "y2": 580},
            review_status="Accepted",
            note="Visible deformation on the left door panel.",
        ),
        Detection(
            detection_id="D-02",
            damage_type="scratch",
            confidence=0.67,
            bbox={"x1": 535, "y1": 385, "x2": 715, "y2": 520},
            review_status="Needs review",
            note="Confirm under neutral lighting; reflection is present.",
        ),
    ]
    inspection = {
        "inspection_id": "GI-20260830-DEMO01",
        "registration": "BA 01 PA 1234",
        "make": "Toyota",
        "model": "Corolla",
        "year": "2020",
        "inspector": "Aayush Phuyal",
        "purpose": "Used-vehicle assessment",
        "created_at_display": "30 Aug 2026, 10:00 AM",
        "source": "Uploaded photo",
    }
    annotated = annotate_image(image, detections)
    pdf = build_pdf_report(
        inspection,
        assess_image_quality(image).to_dict(),
        detections,
        image,
        annotated,
    )
    destination = output_dir / "gaadi-inspector-sample-report.pdf"
    destination.write_bytes(pdf)
    print(destination)


if __name__ == "__main__":
    main()
