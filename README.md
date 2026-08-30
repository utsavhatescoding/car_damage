# Gaadi Inspector

Gaadi Inspector is a mobile-first Streamlit application for AI-assisted visible vehicle damage inspection. It accepts an uploaded photo or a still camera capture, runs the validated CarDD YOLOv8n detector, lets a person review each finding, and exports a professional PDF, annotated image and JSON record. An optional Live Inspection - Beta mode automatically analyses periodic camera frames for product testing without WebRTC, STUN or TURN configuration.

## Product scope

Version 1 supports six visible damage categories:

- Dent
- Scratch
- Crack
- Glass shatter
- Lamp broken
- Tire flat

The application is inspection support—not an autonomous safety, insurance or repair decision system. It does not assess mechanical, structural, underbody or internal vehicle condition.

## Install the validated model

Copy the validated model from Google Drive:

```text
CarDD_Premium_Project/models/cardd_yolov8n_detection_v1/
cardd_yolov8n_detection_v1_best.pt
```

into:

```text
gaadi-inspector/models/cardd_yolov8n_detection_v1_best.pt
```

The repository is configured to allow this exact production model filename to be committed so Streamlit Community Cloud can load it. Only commit the weights when your data and framework licences allow redistribution.

## Run on macOS

Python 3.11 is recommended.

```bash
cd gaadi-inspector
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. For camera capture, allow browser camera permission. A deployed HTTPS app is normally required for camera access outside localhost.

## Alternative model location

Set `GAADI_MODEL_PATH` to use a model outside the project:

```bash
export GAADI_MODEL_PATH="/absolute/path/to/best.pt"
streamlit run app.py
```

## Validate the project

```bash
python -m compileall app.py src tests
pip install pytest
pytest -q
```

## Deployment notes

- Put `requirements.txt` in the repository root with `app.py` (already configured).
- Add the validated 6.2 MB model at the exact path shown above before pushing.
- Connect the GitHub repository in Streamlit Community Cloud and select `app.py` as the entrypoint.
- Choose Python 3.12 in Advanced settings so local and hosted environments can match.
- Community Cloud serves the app over HTTPS, which is required for remote camera access.
- Live Inspection uses automatic browser camera snapshots over Streamlit's normal app connection. It does not require STUN or TURN configuration.
- Live Inspection requests the rear camera first on supported phones and includes a compact Flip control.
- Keep the model and source licences documented.
- Use private or approved model storage when weights cannot be redistributed.
- Vehicle images sent to a remotely hosted Streamlit app are processed on that host.
- Add a privacy notice and retention policy before collecting real customer images.
- Do not imply police, government, insurer or licensed-surveyor affiliation.
- The included social-preview artwork is `assets/social-preview.png`; set it as the repository social preview manually when publishing on GitHub.

## Project structure

```text
gaadi-inspector/
├── .streamlit/config.toml
├── app.py
├── assets/
│   ├── favicon.svg
│   ├── logo.svg
│   └── social-preview.png
├── models/
├── src/
│   ├── brand.py
│   ├── image_quality.py
│   ├── live_camera.py
│   ├── model_service.py
│   └── report_service.py
├── tests/test_core.py
└── requirements.txt
```
