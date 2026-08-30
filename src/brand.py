from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

BRAND = {
    "name": "Gaadi Inspector",
    "tagline": "Evidence-led vehicle inspection",
    "navy": "#07192E",
    "blue": "#2F7CF6",
    "cyan": "#54C7FF",
    "red": "#F04455",
    "ink": "#102033",
    "muted": "#64748B",
    "paper": "#F3F6FA",
    "white": "#FFFFFF",
}


def load_svg(filename: str) -> str:
    return (ASSETS / filename).read_text(encoding="utf-8")


def app_css() -> str:
    """Return the responsive visual system for the Streamlit app."""
    return """
    <style>
      :root {
        --gi-navy: #07192E;
        --gi-navy-2: #102D50;
        --gi-blue: #2F7CF6;
        --gi-cyan: #54C7FF;
        --gi-red: #F04455;
        --gi-ink: #102033;
        --gi-muted: #64748B;
        --gi-border: #DCE5EF;
        --gi-paper: #F3F6FA;
        --gi-white: #FFFFFF;
        --gi-green: #1B9C6B;
      }

      html, body, [class*="css"] { font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      .stApp { background: linear-gradient(180deg, #ECF2F8 0, #F6F8FB 320px, #F3F6FA 100%); color: var(--gi-ink); }
      [data-testid="stHeader"] { background: rgba(243,246,250,.86); backdrop-filter: blur(16px); }
      [data-testid="stToolbar"], #MainMenu, footer { visibility: hidden; }
      .block-container { max-width: 1120px; padding-top: 1.15rem; padding-bottom: 4rem; }

      .gi-topbar { display:flex; align-items:center; justify-content:space-between; gap:20px; margin: 0 0 18px; }
      .gi-brand { display:flex; align-items:center; gap:12px; }
      .gi-brand-logo { width:48px; height:48px; filter: drop-shadow(0 8px 13px rgba(7,25,46,.18)); }
      .gi-brand-logo svg { display:block; width:100%; height:100%; }
      .gi-brand-title { font-size:1.14rem; line-height:1.05; font-weight:800; letter-spacing:-.02em; color:var(--gi-navy); }
      .gi-brand-sub { margin-top:4px; color:var(--gi-muted); font-size:.78rem; font-weight:600; letter-spacing:.02em; }
      .gi-status { display:inline-flex; align-items:center; gap:8px; border:1px solid #CFE0F2; background:rgba(255,255,255,.72); padding:9px 13px; border-radius:999px; color:#35506E; font-size:.76rem; font-weight:700; }
      .gi-status-dot { width:8px; height:8px; border-radius:50%; background:var(--gi-green); box-shadow:0 0 0 4px rgba(27,156,107,.12); }

      .gi-hero { position:relative; overflow:hidden; color:white; border-radius:28px; padding:36px 38px; background:linear-gradient(126deg,#07192E 0%,#102D50 72%,#173B68 100%); box-shadow:0 22px 55px rgba(7,25,46,.16); margin-bottom:22px; }
      .gi-hero:after { content:""; position:absolute; width:310px; height:310px; border:1px solid rgba(84,199,255,.18); border-radius:50%; right:-65px; top:-145px; box-shadow:0 0 0 52px rgba(84,199,255,.035),0 0 0 104px rgba(84,199,255,.025); }
      .gi-kicker { display:inline-flex; align-items:center; gap:9px; text-transform:uppercase; color:#A8DDFF; letter-spacing:.13em; font-size:.72rem; font-weight:800; }
      .gi-kicker-line { width:26px; height:2px; background:linear-gradient(90deg,var(--gi-blue),var(--gi-red)); border-radius:2px; }
      .gi-hero h1 { margin:13px 0 10px; max-width:720px; color:white; font-size:clamp(2rem,5vw,3.35rem); line-height:1.03; letter-spacing:-.045em; }
      .gi-hero p { margin:0; max-width:680px; color:#C4D5E7; font-size:1rem; line-height:1.65; }
      .gi-hero-meta { display:flex; flex-wrap:wrap; gap:10px; margin-top:24px; }
      .gi-chip { border:1px solid rgba(255,255,255,.14); background:rgba(255,255,255,.07); color:#DCEBFA; border-radius:999px; padding:8px 12px; font-size:.76rem; font-weight:650; }

      .gi-section-head { margin:27px 0 13px; display:flex; align-items:flex-end; justify-content:space-between; gap:15px; }
      .gi-section-head h2 { margin:0; color:var(--gi-navy); font-size:1.25rem; letter-spacing:-.025em; }
      .gi-section-head p { margin:4px 0 0; color:var(--gi-muted); font-size:.84rem; }
      .gi-step { color:var(--gi-blue); font-size:.72rem; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }

      [data-testid="stForm"], [data-testid="stExpander"], div[data-testid="stFileUploader"], div[data-testid="stCameraInput"] { background:rgba(255,255,255,.92); border:1px solid var(--gi-border); border-radius:18px; box-shadow:0 8px 24px rgba(22,50,78,.055); }
      [data-testid="stForm"] { padding:18px 20px 8px; }
      div[data-testid="stFileUploader"], div[data-testid="stCameraInput"] { padding:8px; }
      [data-testid="stFileUploaderDropzone"] { background:#F8FAFD; border:1.5px dashed #BDD0E3; border-radius:14px; }
      button[kind="primary"] { border:0 !important; background:linear-gradient(100deg,#216EE7,#388BFF) !important; border-radius:12px !important; font-weight:750 !important; min-height:46px; box-shadow:0 10px 22px rgba(47,124,246,.22); }
      button[kind="secondary"] { border:1px solid #C9D7E6 !important; background:white !important; color:var(--gi-navy) !important; border-radius:12px !important; min-height:44px; font-weight:700 !important; }
      [data-baseweb="tab-list"] { background:#E8EEF5; padding:5px; border-radius:14px; gap:4px; }
      [data-baseweb="tab"] { height:46px; border-radius:10px; font-weight:750; }
      [aria-selected="true"][data-baseweb="tab"] { background:white; box-shadow:0 5px 14px rgba(22,50,78,.09); }
      [data-testid="stMetric"] { background:white; border:1px solid var(--gi-border); padding:15px 16px; border-radius:16px; box-shadow:0 7px 22px rgba(22,50,78,.045); }
      [data-testid="stMetricLabel"] { color:var(--gi-muted); }
      [data-testid="stImage"] img { border-radius:18px; }
      .stDownloadButton button { width:100%; }

      .gi-quality { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:12px 0 4px; }
      .gi-quality-item { background:white; border:1px solid var(--gi-border); border-radius:14px; padding:13px; }
      .gi-quality-label { color:var(--gi-muted); font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
      .gi-quality-value { color:var(--gi-navy); font-size:.96rem; font-weight:800; margin-top:4px; }
      .gi-quality-good { color:var(--gi-green); }
      .gi-quality-warn { color:#C06C17; }

      .gi-alert { display:flex; gap:12px; align-items:flex-start; border-radius:14px; padding:14px 15px; margin:10px 0; font-size:.86rem; line-height:1.5; }
      .gi-alert-info { background:#EAF3FF; border:1px solid #C6DEFF; color:#174E91; }
      .gi-alert-warning { background:#FFF6E8; border:1px solid #F2D5A9; color:#855017; }
      .gi-alert-success { background:#EAF8F2; border:1px solid #BCE5D2; color:#176345; }

      .gi-detection { border-left:4px solid var(--gi-blue); background:white; border-radius:4px 15px 15px 4px; padding:13px 15px; margin:10px 0; box-shadow:0 6px 18px rgba(22,50,78,.05); }
      .gi-detection-title { font-weight:800; color:var(--gi-navy); text-transform:capitalize; }
      .gi-confidence { color:var(--gi-blue); font-weight:800; }
      .gi-small { color:var(--gi-muted); font-size:.78rem; }

      .gi-footer { margin-top:38px; padding-top:20px; border-top:1px solid #DCE5EF; display:flex; justify-content:space-between; gap:18px; color:#6B7E91; font-size:.75rem; line-height:1.5; }
      .gi-emergency { display:flex; height:4px; width:100%; margin-bottom:18px; overflow:hidden; border-radius:4px; }
      .gi-emergency span:first-child { width:50%; background:var(--gi-blue); }
      .gi-emergency span:last-child { width:50%; background:var(--gi-red); }

      @media (max-width: 720px) {
        .block-container { padding: .75rem .85rem 3rem; }
        .gi-topbar { margin-bottom:12px; }
        .gi-brand-logo { width:41px; height:41px; }
        .gi-brand-sub { display:none; }
        .gi-status { font-size:.66rem; padding:7px 10px; }
        .gi-hero { padding:27px 22px; border-radius:22px; }
        .gi-hero p { font-size:.9rem; line-height:1.55; }
        .gi-hero-meta { margin-top:18px; gap:7px; }
        .gi-chip { font-size:.68rem; padding:7px 9px; }
        .gi-section-head { margin-top:22px; align-items:flex-start; flex-direction:column; gap:5px; }
        .gi-quality { grid-template-columns:1fr; }
        [data-testid="column"] { min-width:100% !important; }
        [data-testid="stHorizontalBlock"] { gap:.65rem; flex-wrap:wrap; }
        .gi-footer { flex-direction:column; }
      }
    </style>
    """
