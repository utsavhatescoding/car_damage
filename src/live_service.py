from __future__ import annotations

import threading
from collections.abc import Callable

import av
import cv2

from .model_service import CLASS_COLOURS


def _hex_to_bgr(hex_colour: str) -> tuple[int, int, int]:
    value = hex_colour.lstrip("#")
    red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    return blue, green, red


def draw_live_detections(frame, detections: list[dict], provisional: bool = True):
    """Draw high-contrast provisional boxes on a BGR camera frame."""
    canvas = frame.copy()
    height, width = canvas.shape[:2]
    line_width = max(2, round(min(width, height) / 260))

    for detection in detections:
        x1, y1, x2, y2 = [int(value) for value in detection["bbox"]]
        damage_type = detection["damage_type"]
        confidence = detection["confidence"]
        colour = _hex_to_bgr(CLASS_COLOURS.get(damage_type, "#2F7CF6"))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), colour, line_width)

        prefix = "POSSIBLE " if provisional else ""
        label = f"{prefix}{damage_type.upper()} {confidence:.0%}"
        font_scale = max(0.48, min(width, height) / 1100)
        text_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        label_y = max(text_size[1] + 12, y1)
        cv2.rectangle(
            canvas,
            (x1, label_y - text_size[1] - 12),
            (min(width - 1, x1 + text_size[0] + 16), label_y + baseline + 2),
            colour,
            -1,
        )
        cv2.putText(
            canvas,
            label,
            (x1 + 8, label_y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    banner = "LIVE BETA - PROVISIONAL DETECTIONS"
    cv2.rectangle(canvas, (0, 0), (width, max(38, height // 16)), (7, 25, 46), -1)
    cv2.putText(
        canvas,
        banner,
        (14, max(27, height // 23)),
        cv2.FONT_HERSHEY_SIMPLEX,
        max(0.5, min(width, height) / 1200),
        (84, 199, 255),
        2,
        cv2.LINE_AA,
    )
    return canvas


def create_live_callback(model, confidence: float, frame_stride: int = 3) -> Callable:
    """Create a thread-safe WebRTC callback that samples frames for YOLO inference."""
    lock = threading.Lock()
    state = {"frame_number": 0, "detections": []}

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")

        with lock:
            state["frame_number"] += 1
            should_infer = state["frame_number"] == 1 or state["frame_number"] % frame_stride == 0

        if should_infer:
            try:
                result = model.predict(
                    source=image,
                    conf=confidence,
                    iou=0.45,
                    imgsz=640,
                    max_det=30,
                    verbose=False,
                )[0]
                fresh_detections = []
                for box in result.boxes:
                    class_id = int(box.cls.item())
                    fresh_detections.append(
                        {
                            "damage_type": model.names[class_id],
                            "confidence": float(box.conf.item()),
                            "bbox": [float(value) for value in box.xyxy[0].tolist()],
                        }
                    )
                with lock:
                    state["detections"] = fresh_detections
            except Exception:
                # A transient frame must not terminate the camera stream.
                pass

        with lock:
            latest = list(state["detections"])

        annotated = draw_live_detections(image, latest, provisional=True)
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

    return video_frame_callback

