from __future__ import annotations

import base64
import io
from pathlib import Path

import streamlit.components.v1 as components


_FRONTEND = Path(__file__).resolve().parents[1] / "assets" / "live-camera"
_camera_component = components.declare_component("gaadi_live_camera", path=str(_FRONTEND))


def live_camera(*, interval_ms: int = 1200, key: str = "gaadi-live-camera") -> io.BytesIO | None:
    """Open a mobile-friendly camera and return automatic JPEG snapshots."""
    value = _camera_component(intervalMs=interval_ms, key=key, default=None)
    if not value or "," not in value:
        return None
    _, encoded = value.split(",", 1)
    return io.BytesIO(base64.b64decode(encoded))
