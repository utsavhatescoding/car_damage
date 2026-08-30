from __future__ import annotations

import io
import uuid
from datetime import datetime

import streamlit as st
from PIL import Image

from src.brand import ASSETS, app_css, load_svg
from src.image_quality import assess_image_quality, normalize_orientation
from src.live_service import create_live_callback
from src.model_service import CLASS_NAMES, Detection, annotate_image, load_model, resolve_model_path, run_inference
from src.report_service import build_json_report, build_pdf_report, report_payload


st.set_page_config(
    page_title="Gaadi Inspector | AI Vehicle Damage Inspection",
    page_icon=str(ASSETS / "favicon.svg"),
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Gaadi Inspector — AI-assisted visible vehicle damage inspection.",
    },
)

st.markdown(app_css(), unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def cached_model():
    return load_model()


def new_inspection_id() -> str:
    return f"GI-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def image_as_png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def reset_result() -> None:
    for key in ("detections", "inference_ms", "reviewed", "source_image_key"):
        st.session_state.pop(key, None)


if "inspection_id" not in st.session_state:
    st.session_state.inspection_id = new_inspection_id()

logo_svg = load_svg("logo.svg")
st.markdown(
    f"""
    <div class="gi-topbar">
      <div class="gi-brand">
        <div class="gi-brand-logo">{logo_svg}</div>
        <div>
          <div class="gi-brand-title">Gaadi Inspector</div>
          <div class="gi-brand-sub">Evidence-led vehicle inspection</div>
        </div>
      </div>
      <div class="gi-status"><span class="gi-status-dot"></span> AI-assisted system</div>
    </div>
    <div class="gi-hero">
      <div class="gi-kicker"><span class="gi-kicker-line"></span> Visible damage intelligence</div>
      <h1>Inspect with clarity.<br/>Report with confidence.</h1>
      <p>Upload or capture a vehicle photo, identify possible visible damage, review every finding and produce an evidence-ready inspection report.</p>
      <div class="gi-hero-meta">
        <span class="gi-chip">6 damage categories</span>
        <span class="gi-chip">Human review controls</span>
        <span class="gi-chip">Professional PDF report</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="gi-section-head">
      <div><h2>Inspection details</h2><p>Add context so the result is useful beyond the screen.</p></div>
      <div class="gi-step">Step 01</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("inspection_details", border=True):
    row_one = st.columns(3)
    registration = row_one[0].text_input("Registration number", placeholder="BA 01 PA 1234").strip().upper()
    make = row_one[1].text_input("Make", placeholder="Toyota").strip()
    model_name = row_one[2].text_input("Model", placeholder="Corolla").strip()

    row_two = st.columns(3)
    year = row_two[0].text_input("Year", placeholder="2020", max_chars=4).strip()
    inspector = row_two[1].text_input("Inspector / operator", placeholder="Full name").strip()
    purpose = row_two[2].selectbox("Inspection purpose", ["General visible-damage check", "Used-vehicle assessment", "Workshop intake", "Insurance pre-check", "Fleet return", "Other"])
    st.form_submit_button("Save inspection details", use_container_width=True)

inspection = {
    "inspection_id": st.session_state.inspection_id,
    "registration": registration,
    "make": make,
    "model": model_name,
    "year": year,
    "inspector": inspector,
    "purpose": purpose,
    "created_at_display": datetime.now().strftime("%d %b %Y, %I:%M %p"),
}

st.markdown(
    """
    <div class="gi-section-head">
      <div><h2>Add vehicle evidence</h2><p>Use a clear, stable image showing the damaged area and surrounding panel.</p></div>
      <div class="gi-step">Step 02</div>
    </div>
    """,
    unsafe_allow_html=True,
)

upload_tab, camera_tab, live_tab = st.tabs(["Upload photo", "Use camera", "Live inspection - Beta"])

with upload_tab:
    uploaded_file = st.file_uploader(
        "Upload a vehicle image",
        type=["jpg", "jpeg", "png", "webp"],
        help="Maximum 20 MB. JPEG, PNG or WebP.",
        label_visibility="collapsed",
    )

with camera_tab:
    camera_file = st.camera_input(
        "Capture a vehicle image",
        help="On mobile, allow camera access and use the rear camera when available.",
        label_visibility="collapsed",
    )

with live_tab:
    st.markdown(
        '<div class="gi-alert gi-alert-warning">⚠️ <div><strong>Testing mode.</strong> Live boxes are provisional and are not included in an inspection report. Use Upload photo or Use camera for report-grade analysis.</div></div>',
        unsafe_allow_html=True,
    )
    live_controls = st.columns(2)
    live_confidence = live_controls[0].slider(
        "Live confidence",
        min_value=0.15,
        max_value=0.90,
        value=0.35,
        step=0.05,
        key="live_confidence",
        help="Lower values display more possible damage and more false alerts.",
    )
    live_stride = live_controls[1].select_slider(
        "Analyse every",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda value: f"{value} frame" if value == 1 else f"{value} frames",
        help="A larger interval reduces server work during testing.",
    )

    model_path = resolve_model_path()
    if not model_path.exists():
        st.error("Install the validated model weights before starting live inspection.")
    else:
        try:
            from streamlit_webrtc import WebRtcMode, webrtc_streamer

            webrtc_streamer(
                key="gaadi-live-inspection",
                mode=WebRtcMode.SENDRECV,
                video_frame_callback=create_live_callback(
                    cached_model(),
                    confidence=live_confidence,
                    frame_stride=live_stride,
                ),
                rtc_configuration={
                    "iceServers": [
                        {"urls": ["stun:stun.l.google.com:19302"]}
                    ]
                },
                media_stream_constraints={
                    "video": {
                        "facingMode": {"ideal": "environment"},
                        "width": {"ideal": 1280},
                        "height": {"ideal": 720},
                    },
                    "audio": False,
                },
                video_html_attrs={
                    "autoPlay": True,
                    "controls": False,
                    "muted": True,
                    "playsInline": True,
                },
                media_toggle_controls=False,
            )
            st.caption(
                "Point the rear camera at one vehicle area and move slowly. "
                "For small damage, stop movement and move closer."
            )
        except ImportError:
            st.error("Live inspection dependencies are missing. Run: pip install -r requirements.txt")

source_file = camera_file or uploaded_file
source_name = "Camera capture" if camera_file else "Uploaded photo"

if source_file:
    source_bytes = source_file.getvalue()
    source_key = f"{source_file.name}:{len(source_bytes)}:{hash(source_bytes[:4096])}"
    if st.session_state.get("source_image_key") not in (None, source_key):
        reset_result()

    try:
        original_image = normalize_orientation(Image.open(io.BytesIO(source_bytes)))
    except Exception:
        st.error("This image could not be opened. Please choose a valid JPEG, PNG or WebP file.")
        st.stop()

    quality = assess_image_quality(original_image)
    inspection["source"] = source_name

    preview_column, details_column = st.columns([1.45, 1], gap="large")
    with preview_column:
        st.image(original_image, caption="Inspection image", use_container_width=True)

    with details_column:
        st.markdown("#### Capture quality")
        quality_class = "gi-quality-good" if quality.acceptable else "gi-quality-warn"
        st.markdown(
            f"""
            <div class="gi-quality">
              <div class="gi-quality-item"><div class="gi-quality-label">Resolution</div><div class="gi-quality-value {quality_class}">{quality.width} × {quality.height}</div></div>
              <div class="gi-quality-item"><div class="gi-quality-label">Lighting</div><div class="gi-quality-value {quality_class}">{quality.brightness_status}</div></div>
              <div class="gi-quality-item"><div class="gi-quality-label">Sharpness</div><div class="gi-quality-value {quality_class}">{quality.sharpness_status}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if quality.warnings:
            for warning in quality.warnings:
                st.markdown(f'<div class="gi-alert gi-alert-warning">⚠️ <div>{warning}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="gi-alert gi-alert-success">✓ <div>Image quality checks passed.</div></div>', unsafe_allow_html=True)

        confidence = st.slider(
            "Detection confidence",
            min_value=0.10,
            max_value=0.90,
            value=0.35,
            step=0.05,
            help="Lower values find more possible damage but may increase false alerts.",
        )

        model_path = resolve_model_path()
        if not model_path.exists():
            st.error("Model weights are not installed yet.")
            st.code(str(model_path), language=None)
            st.caption("Copy the validated best.pt file to this location, then restart the app.")
        elif st.button("Analyse visible damage", type="primary", use_container_width=True):
            with st.spinner("Examining the vehicle image…"):
                try:
                    detections, inference_ms = run_inference(cached_model(), original_image, confidence=confidence)
                    st.session_state.detections = [item.to_dict() for item in detections]
                    st.session_state.inference_ms = inference_ms
                    st.session_state.source_image_key = source_key
                    st.session_state.reviewed = False
                except Exception as error:
                    st.error(f"Inspection could not be completed: {error}")

    if "detections" in st.session_state and st.session_state.get("source_image_key") == source_key:
        detections = [Detection(**item) for item in st.session_state.detections]
        annotated_image = annotate_image(original_image, detections)

        st.markdown(
            """
            <div class="gi-section-head">
              <div><h2>AI inspection result</h2><p>Every finding is provisional until reviewed by a person.</p></div>
              <div class="gi-step">Step 03</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_columns = st.columns(3)
        metric_columns[0].metric("Possible damage", len(detections))
        metric_columns[1].metric("Highest confidence", f"{max((item.confidence for item in detections), default=0):.0%}")
        metric_columns[2].metric("Inference time", f"{st.session_state.inference_ms:.0f} ms")

        original_view, annotated_view = st.tabs(["Original", "AI annotated"])
        with original_view:
            st.image(original_image, use_container_width=True)
        with annotated_view:
            st.image(annotated_image, use_container_width=True)

        if not detections:
            st.markdown(
                '<div class="gi-alert gi-alert-info">ℹ️ <div>No supported visible damage was detected above the selected threshold. This does not confirm that the vehicle is damage-free; inspect the image manually.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("#### Detection review")
            st.caption("Accept valid findings, reject false alerts, or leave uncertain findings for review.")

            updated: list[Detection] = []
            for index, detection in enumerate(detections):
                with st.expander(
                    f"{detection.detection_id}  ·  {detection.damage_type.title()}  ·  {detection.confidence:.0%}",
                    expanded=index == 0,
                ):
                    review_columns = st.columns([1, 1, 1.5])
                    detection.damage_type = review_columns[0].selectbox(
                        "Damage type",
                        CLASS_NAMES,
                        index=CLASS_NAMES.index(detection.damage_type),
                        key=f"type_{source_key}_{detection.detection_id}",
                    )
                    detection.review_status = review_columns[1].selectbox(
                        "Review decision",
                        ["Needs review", "Accepted", "Rejected"],
                        index=["Needs review", "Accepted", "Rejected"].index(detection.review_status),
                        key=f"status_{source_key}_{detection.detection_id}",
                    )
                    detection.note = review_columns[2].text_input(
                        "Inspector note",
                        value=detection.note,
                        placeholder="Optional observation",
                        key=f"note_{source_key}_{detection.detection_id}",
                    )
                    st.markdown(
                        f'<div class="gi-detection"><div class="gi-detection-title">{detection.damage_type} <span class="gi-confidence">{detection.confidence:.1%}</span></div><div class="gi-small">AI confidence is not damage severity. Verify the visible area before accepting.</div></div>',
                        unsafe_allow_html=True,
                    )
                    updated.append(detection)

            if st.button("Apply review decisions", use_container_width=True):
                st.session_state.detections = [item.to_dict() for item in updated]
                st.session_state.reviewed = all(item.review_status != "Needs review" for item in updated)
                st.rerun()

        detections = [Detection(**item) for item in st.session_state.detections]
        annotated_image = annotate_image(original_image, detections)

        st.markdown(
            """
            <div class="gi-section-head">
              <div><h2>Inspection package</h2><p>Download the reviewed evidence and structured record.</p></div>
              <div class="gi-step">Step 04</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        payload = report_payload(inspection, quality.to_dict(), detections, st.session_state.inference_ms)
        pdf_bytes = build_pdf_report(inspection, quality.to_dict(), detections, original_image, annotated_image)
        json_bytes = build_json_report(payload)
        safe_id = inspection["inspection_id"].lower()

        download_columns = st.columns(3)
        download_columns[0].download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name=f"{safe_id}-inspection-report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
        download_columns[1].download_button(
            "Download annotated image",
            data=image_as_png(annotated_image),
            file_name=f"{safe_id}-annotated.png",
            mime="image/png",
            use_container_width=True,
        )
        download_columns[2].download_button(
            "Download JSON record",
            data=json_bytes,
            file_name=f"{safe_id}-inspection.json",
            mime="application/json",
            use_container_width=True,
        )

        if st.button("Start a new inspection", use_container_width=True):
            st.session_state.clear()
            st.rerun()

else:
    st.markdown(
        '<div class="gi-alert gi-alert-info">ⓘ <div>For the clearest result, photograph one vehicle area at a time in even light. Avoid glare, heavy shadows and motion blur.</div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="gi-footer">
      <div><strong>Gaadi Inspector</strong><br/>Independent AI-assisted inspection support.</div>
      <div>This system evaluates supported visible exterior damage only. It is not affiliated with, endorsed by or operated by any police or government authority. Human verification is required.</div>
    </div>
    <div class="gi-emergency"><span></span><span></span></div>
    """,
    unsafe_allow_html=True,
)
