from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps


@dataclass(frozen=True)
class QualityResult:
    width: int
    height: int
    megapixels: float
    brightness: float
    sharpness: float
    resolution_status: str
    brightness_status: str
    sharpness_status: str
    warnings: tuple[str, ...]

    @property
    def acceptable(self) -> bool:
        return len(self.warnings) == 0

    def to_dict(self) -> dict:
        result = asdict(self)
        result["acceptable"] = self.acceptable
        return result


def normalize_orientation(image: Image.Image) -> Image.Image:
    """Apply phone EXIF rotation and return an RGB image."""
    return ImageOps.exif_transpose(image).convert("RGB")


def assess_image_quality(image: Image.Image) -> QualityResult:
    image = normalize_orientation(image)
    rgb = np.asarray(image)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    width, height = image.size
    megapixels = (width * height) / 1_000_000
    brightness = float(gray.mean())
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    warnings: list[str] = []

    if min(width, height) < 480:
        resolution_status = "Low"
        warnings.append("Image resolution is low. Move closer or use the original camera photo.")
    else:
        resolution_status = "Good"

    if brightness < 45:
        brightness_status = "Too dark"
        warnings.append("The image is dark. Retake it in brighter, even lighting.")
    elif brightness > 220:
        brightness_status = "Too bright"
        warnings.append("The image is overexposed. Reduce glare or change the camera angle.")
    else:
        brightness_status = "Good"

    if sharpness < 55:
        sharpness_status = "Blurry"
        warnings.append("The image may be blurry. Hold the phone steady and retake it.")
    else:
        sharpness_status = "Good"

    return QualityResult(
        width=width,
        height=height,
        megapixels=round(megapixels, 2),
        brightness=round(brightness, 1),
        sharpness=round(sharpness, 1),
        resolution_status=resolution_status,
        brightness_status=brightness_status,
        sharpness_status=sharpness_status,
        warnings=tuple(warnings),
    )

