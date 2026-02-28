
import os, tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from pipeline import detect_defects, assess_severity, reason_root_causes, draw_annotations, generate_report, generate_pdf_report

load_dotenv()

# Page Config 
st.set_page_config(page_title="Defect Inspector", layout="wide")

# global styles
st.markdown("""
<style>
/* overall background */
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stHeader"] { background: transparent; }

/* sidebar */
section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }

/* cards */
.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.card-title { font-size: 15px; font-weight: 700; color: #e6edf3; margin-bottom: 6px; }
.card-meta  { font-size: 12px; color: #8b949e; margin-bottom: 8px; }
.card-body  { font-size: 13px; color: #c9d1d9; line-height: 1.7; }

/* severity badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-High   { background:#3d1a1a; color:#ff6b6b; border:1px solid #ff4444; }
.badge-Medium { background:#2d2010; color:#ffa940; border:1px solid #fa8c16; }
.badge-Low    { background:#0d2a1a; color:#52c41a; border:1px solid #389e0d; }

/* score bar */
.score-bar-bg {
    background: #21262d;
    border-radius: 4px;
    height: 6px;
    width: 100%;
    margin-top: 6px;
}
.score-bar-fill {
    height: 6px;
    border-radius: 4px;
}

/* verdict boxes */
.verdict-pass  { background:#0d2a1a; border:1px solid #389e0d; border-radius:8px; padding:14px 20px; color:#52c41a; }
.verdict-warn  { background:#2d2010; border:1px solid #fa8c16; border-radius:8px; padding:14px 20px; color:#ffa940; }
.verdict-fail  { background:#3d1a1a; border:1px solid #ff4444; border-radius:8px; padding:14px 20px; color:#ff6b6b; }

/* divider */
hr { border-color: #30363d !important; }

/* image captions */
.img-caption { text-align:center; font-size:12px; color:#8b949e; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# header
st.markdown("## Defect Inspection System")
st.markdown("<span style='color:#8b949e;font-size:14px;'>Upload an industrial image to detect, score, and analyze surface defects.</span>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

# upload 
uploaded = st.file_uploader("Upload inspection image", type=["jpg", "jpeg", "png", "bmp", "webp"],
                             label_visibility="collapsed")

if uploaded is None:
    st.markdown("""
    <div style='text-align:center;padding:60px 20px;color:#8b949e;border:1px dashed #30363d;border-radius:10px;'>
        <div style='font-size:15px;'>Drag & drop an image here, or click <b>Browse files</b></div>
        <div style='font-size:12px;margin-top:6px;'>Supports JPG · JPEG · PNG · BMP · WEBP</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

img = Image.open(uploaded)
_, mid, _ = st.columns([3, 2, 3])
with mid:
    st.image(img, width=320)
    st.markdown(f"<div class='img-caption'>{uploaded.name}</div>", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)
run = st.button("Run Inspection", type="primary", use_container_width=True)
if not run:
    st.stop()

if not os.getenv("ROBOFLOW_API_KEY"):
    st.error("ROBOFLOW_API_KEY not set in your .env file.")
    st.stop()

# pipeline 
img_rgb = img.convert("RGB") if img.mode == "RGBA" else img
tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
img_rgb.save(tmp.name)
tmp_path = tmp.name
tmp.close()

cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
img_h, img_w = cv_img.shape[:2]

progress = st.progress(0, text="Step 1 / 3 — Detecting defects…")
try:
    found_defects = detect_defects(tmp_path)
except Exception as err:
    st.error(f"Detection failed: {err}")
    os.unlink(tmp_path)
    st.stop()

if not found_defects:
    progress.empty()
    st.markdown("<div class='verdict-pass'><b>PASS</b> — No defects detected. Component looks good.</div>", unsafe_allow_html=True)
    os.unlink(tmp_path)
    st.stop()

progress.progress(33, text="Step 2 / 3 — Scoring severity…")
found_defects = assess_severity(found_defects, img_w, img_h)

progress.progress(66, text="Step 3 / 3 — Analyzing root causes…")
found_defects, gemini_err = reason_root_causes(found_defects)
progress.progress(100, text="Done.")
progress.empty()

# annotated image 
marked_img = draw_annotations(cv_img, found_defects)
marked_rgb = cv2.cvtColor(marked_img, cv2.COLOR_BGR2RGB)

st.markdown("<hr/>", unsafe_allow_html=True)
_, col_orig, col_ann, _ = st.columns([1, 2, 2, 1])
with col_orig:
    st.image(img, width=340)
    st.markdown("<div class='img-caption'>Original Image</div>", unsafe_allow_html=True)
with col_ann:
    st.image(marked_rgb, width=340)
    st.markdown("<div class='img-caption'>Annotated — Defects Marked</div>", unsafe_allow_html=True)

# results 
st.markdown("<hr/>", unsafe_allow_html=True)
col_summary, col_causes = st.columns(2)

SEV_COLOR = {"High": "#ff6b6b", "Medium": "#ffa940", "Low": "#52c41a"}
BADGE_CLASS = {"High": "badge-High", "Medium": "badge-Medium", "Low": "badge-Low"}

with col_summary:
    st.markdown("#### Defect Summary")
    for idx, d in enumerate(found_defects, 1):
        sev = d["severity_level"]
        bar_color = SEV_COLOR.get(sev, "#888")
        score = d["severity_score"]
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>#{idx} &nbsp; {d['type']} &nbsp;
                <span class='badge {BADGE_CLASS.get(sev,"")}'>{sev}</span>
            </div>
            <div class='card-meta'>
                Location: {d['location']} &nbsp;·&nbsp;
                Confidence: {int(d['confidence']*100)}%
            </div>
            <table style='font-size:12px;color:#8b949e;width:100%;margin:6px 0 8px 0;border-collapse:collapse;'>
              <tr><td style='padding:2px 0;'>Surface Coverage</td><td style='padding:2px 0;text-align:right;color:#c9d1d9;'>{d['size_percent']}%</td></tr>
            </table>
            <div style='font-size:12px;color:#8b949e;margin-bottom:4px;'>Severity Score: <b style='color:{bar_color};'>{score}/100</b></div>
            <div class='score-bar-bg'>
                <div class='score-bar-fill' style='width:{score}%;background:{bar_color};'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_causes:
    st.markdown("#### Root Cause Analysis")
    if gemini_err:
        st.warning(gemini_err)
    for d in found_defects:
        sev = d["severity_level"]
        causes  = d.get("causes", [])
        risks   = d.get("risks", [])
        actions = d.get("actions", [])
        source  = d.get("reasoning_source", "rule-based")

        causes_html  = "".join(f"<li>{c}</li>" for c in causes)
        risks_html   = "".join(f"<li>{r}</li>" for r in risks)
        actions_html = "".join(f"<li>{a}</li>" for a in actions)

        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>{d['type']} &nbsp;
                <span class='badge {BADGE_CLASS.get(sev,"")}'>{sev}</span>
            </div>
            <div class='card-body'>
                <b>Causes</b><ul style='margin:4px 0 8px 16px;padding:0;'>{causes_html}</ul>
                <b>Risks</b><ul style='margin:4px 0 8px 16px;padding:0;'>{risks_html}</ul>
                <b>Recommended Actions</b><ul style='margin:4px 0 8px 16px;padding:0;'>{actions_html}</ul>
            </div>
            <div style='font-size:11px;color:#8b949e;'>Source: {source}</div>
        </div>
        """, unsafe_allow_html=True)

# overall verdict 
st.markdown("<hr/>", unsafe_allow_html=True)
high_count = sum(1 for d in found_defects if d["severity_level"] == "High")
total = len(found_defects)

if high_count > 0:
    st.markdown(f"<div class='verdict-fail'><b>FAIL</b> — {high_count} high-severity defect(s) detected. Immediate action required.</div>", unsafe_allow_html=True)
elif total > 3:
    st.markdown(f"<div class='verdict-warn'><b>WARNING</b> — {total} defects detected. Schedule maintenance soon.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='verdict-pass'><b>PASS WITH NOTES</b> — {total} minor defect(s) found. Monitor in next inspection cycle.</div>", unsafe_allow_html=True)

# download report 
st.markdown("<br/>", unsafe_allow_html=True)
report_text = generate_report(uploaded.name, found_defects)
report_pdf  = generate_pdf_report(uploaded.name, found_defects)
base_name   = uploaded.name.rsplit(".", 1)[0]

col_dl_txt, col_dl_pdf = st.columns(2)
with col_dl_txt:
    st.download_button("Download Report (TXT)", data=report_text,
        file_name=f"report_{base_name}.txt", mime="text/plain",
        use_container_width=True)
with col_dl_pdf:
    st.download_button("Download Report (PDF)", data=report_pdf,
        file_name=f"report_{base_name}.pdf", mime="application/pdf",
        use_container_width=True)

os.unlink(tmp_path)
