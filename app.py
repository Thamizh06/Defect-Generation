import os, tempfile
import cv2, numpy as np, streamlit as st
from PIL import Image
from dotenv import load_dotenv
from pipeline import detect_defects, assess_severity, reason_root_causes, draw_annotations, generate_report

load_dotenv()
st.set_page_config(page_title="Defect Inspector", layout="wide")
st.title("Defect Inspection System")

uploaded = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
if uploaded is None:
    st.stop()

img = Image.open(uploaded)
st.image(img, width=400)
if st.button("Run Inspection"):
    st.write("running...")
