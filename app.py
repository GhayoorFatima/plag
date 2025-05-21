import streamlit as st

# Must be first
st.set_page_config(page_title="AI Plagiarism Checker", layout="wide")

from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher

# Similarity checker
def get_similarity(text1, text2):
    return round(SequenceMatcher(None, text1, text2).ratio() * 100, 2)

# Extract text from uploaded file
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return "\n".join(para.text for para in doc.paragraphs)
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        return "⚠️ Unsupported file format. Please upload a PDF, DOCX, or TXT file."

# UI
st.title("🧠 AI Plagiarism Checker")

st.header("📘 Plagiarism Checker")
col1, col2 = st.columns(2)

with col1:
    uploaded_file1 = st.file_uploader("Upload Original Text File", type=["pdf", "docx", "txt"], key="file1")
    text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)

with col2:
    uploaded_file2 = st.file_uploader("Upload Submitted Text File", type=["pdf", "docx", "txt"], key="file2")
    text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

if st.button("🔍 Check for Plagiarism"):
    if text1.strip() and text2.strip():
        score = get_similarity(text1, text2)
        st.success(f"Similarity Score: **{score}%**")
        if score > 10:
            st.warning("⚠️ High similarity detected. Potential plagiarism.")
        else:
            st.info("✅ Low similarity. Content appears original.")
    else:
        st.error("Both inputs are required.")
