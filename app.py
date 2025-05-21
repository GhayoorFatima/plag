import streamlit as st
from PyPDF2 import PdfReader
import docx

# Set up Streamlit page
st.set_page_config(page_title="AI Plagiarism Checker (Scratch Version)", layout="wide")
st.title("🧠 AI Plagiarism Checker (From Scratch)")

# Text extraction function
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
        return ""

# Clean and tokenize text
def tokenize(text):
    text = text.lower()
    words = ''.join([c if c.isalnum() else ' ' for c in text]).split()
    return set(words)

# Calculate Jaccard similarity
def get_jaccard_similarity(text1, text2):
    words1 = tokenize(text1)
    words2 = tokenize(text2)
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    if not union:
        return 0.0
    similarity = len(intersection) / len(union)
    return round(similarity * 100, 2)

# UI - Input Section
st.header("📘 Upload or Paste Text")
col1, col2 = st.columns(2)

with col1:
    uploaded_file1 = st.file_uploader("Upload Original Document", type=["pdf", "docx", "txt"], key="file1")
    text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)

with col2:
    uploaded_file2 = st.file_uploader("Upload Submitted Document", type=["pdf", "docx", "txt"], key="file2")
    text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

# Plagiarism Check Button
if st.button("🔍 Check for Plagiarism"):
    if text1.strip() and text2.strip():
        similarity = get_jaccard_similarity(text1, text2)
        st.success(f"Similarity Score: **{similarity}%**")
        if similarity > 10:
            st.warning("⚠️ High similarity detected. Potential plagiarism.")
        else:
            st.info("✅ Low similarity. Content appears original.")
    else:
        st.error("Both inputs are required.")
