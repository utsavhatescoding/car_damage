from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .image_quality import normalize_orientation


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT / "models" / "cardd_yolov8n_detection_v1_best.pt"

CLASS_NAMES = [
    "dent",
    "scratch",
    "crack",
    "glass shatter",
    "lamp broken",
    "tire flat",
]

CLASS_COLOURS = {
    "dent": "#2F7CF6",
    "scratch": "#F59E0B",
    "crack": "#A855F7",
    "glass shatter": "#EF4444",
    "lamp broken": "#F04455",
    "tire flat": "#14B8A6",
}


@dataclass
class Detection:
    detection_id: str
    damage_type: str
    confidence: float
    bbox: dict[str, float]
    review_status: str = "Needs review"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_model_path() -> Path:
    configured = os.getenv("GAADI_MODEL_PATH")
    return Path(configured).expanduser() if configured else DEFAULT_MODEL_PATH


def load_model(model_path: Path | None = None):
    from ultralytics import YOLO

    path = model_path or resolve_model_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Model weights were not found at {path}. Copy the validated best.pt "
            "file into the models folder and rename it as documented."
        )
    return YOLO(str(path))


def run_inference(model, image: Image.Image, confidence: float = 0.35, iou: float = 0.45):
    normalized = normalize_orientation(image)
    started = time.perf_counter()
    results = model.predict(
        source=np.asarray(normalized),
        conf=confidence,
        iou=iou,
        imgsz=640,
        max_det=100,
        verbose=False,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000

    detections: list[Detection] = []
    result = results[0]
    for index, box in enumerate(result.boxes):
        class_id = int(box.cls.item())
        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        detections.append(
            Detection(
                detection_id=f"D-{index + 1:02d}",
                damage_type=model.names[class_id],
                confidence=float(box.conf.item()),
                bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            )
        )

    return detections, round(elapsed_ms, 1)


def annotate_image(image: Image.Image, detections: list[Detection]) -> Image.Image:
    canvas = normalize_orientation(image).copy()
    draw = ImageDraw.Draw(canvas, "RGBA")
    font = ImageFont.load_default()
    line_width = max(3, round(min(canvas.size) / 220))

    for detection in detections:
        if detection.review_status == "Rejected":
            continue

        box = detection.bbox
        colour = CLASS_COLOURS.get(detection.damage_type, "#2F7CF6")
        x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
        draw.rectangle((x1, y1, x2, y2), outline=colour, width=line_width)

        label = f"{detection.damage_type.title()}  {detection.confidence:.0%}"
        label_box = draw.textbbox((0, 0), label, font=font)
        label_width = label_box[2] - label_box[0] + 18
        label_height = label_box[3] - label_box[1] + 12
        label_y = max(0, y1 - label_height)
        draw.rounded_rectangle(
            (x1, label_y, x1 + label_width, label_y + label_height),
            radius=5,
            fill=colour,
        )
        draw.text((x1 + 9, label_y + 5), label, fill="white", font=font)

    return canvas

