import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


from ocr.paddle_ocr import (
    OCR_engine_config,
    paddle_text_extractor
)

from ocr.docling_ocr import (
    DocLing_EasyOCR_TextExtractor
)


import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os


# ================================
# Page Config
# ================================
st.set_page_config(
    page_title="Library Stats",
    layout="wide"
)

# ================================
# Data
# ================================
data = {
    "Library": ["DocLing", "PaddleOCR"],
    "Latency_ms": [145, 43129.02],
    "Confidence": [0.85, 0.9594],
}

df = pd.DataFrame(data)

# ================================
# UI Title
# ================================
st.title("📊 Library Stats Comparison")

# ================================
# File Upload
# ================================
st.subheader("📁 Upload Your File")
uploaded_file = st.file_uploader(
    "Upload a resume file",
    type=["pdf", "docx"]
)

if uploaded_file:
    st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")

# ================================
# Combined Latency & Confidence Chart
# ================================
st.subheader("⏱🎯 Latency & Confidence Comparison")

# تحويل البيانات long format عشان Plotly يعمل grouped bars
df_melted = df.melt(
    id_vars="Library",
    value_vars=["Latency_ms", "Confidence"],
    var_name="Metric",
    value_name="Value"
)

# رسم الـ grouped bar chart
combined_fig = px.bar(
    df_melted,
    x="Metric",
    y="Value",
    color="Library",
    barmode="group",
    text="Value",
    title="Latency & Confidence Comparison"
)

combined_fig.update_traces(textposition="outside")
st.plotly_chart(combined_fig, width="stretch")

# ================================
# Text Extraction Comparison
# ================================
st.divider()
st.subheader("🧠 Text Extraction Comparison (Same File)")

if uploaded_file:
    suffix = os.path.splitext(uploaded_file.name)[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        temp_path = tmp.name

    try:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🟦 DocLing")
            with st.spinner("Running DocLing OCR..."):
                docling_text = DocLing_EasyOCR_TextExtractor(
                    temp_path,
                    uploaded_file.name
                )
            st.text_area(
                "DocLing Output",
                docling_text,
                height=420
            )

        with col2:
            st.markdown("### 🟧 PaddleOCR")
            with st.spinner("Running Paddle OCR..."):
                ocr = OCR_engine_config()
                paddle_text = paddle_text_extractor(
                    temp_path,
                    ocr,
                    uploaded_file.name
                )
            st.text_area(
                "Paddle Output",
                paddle_text,
                height=420
            )

    finally:
        os.remove(temp_path)
else:
    st.info("⬆️ Upload a file to compare text extraction outputs.")
