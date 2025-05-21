import streamlit as st
from PyPDF2 import PdfReader
import docx
import math
from collections import Counter

# Set up Streamlit page
st.set_page_config(page_title="AI Plagiarism Checker (Cosine Similarity)", layout="wide")
st.title("🧠 AI Plagiarism Checker using Cosine Similarity (From Scratch)")

# Text extraction
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

# Preprocessing and vectorization
def tokenize(text):
    text = text.lower()
    words = ''.join([c if c.isalnum() else ' ' for c in text]).split()
    return words

def compute_cosine_similarity(text1, text2):
    words1 = tokenize(text1)
    words2 = tokenize(text2)

    freq1 = Counter(words1)
    freq2 = Counter(words2)

    # Vocabulary union
    all_words = set(freq1.keys()).union(set(freq2.keys()))

    # Create vectors
    vec1 = [freq1[word] for word in all_words]
    vec2 = [freq2[word] for word in all_words]

    # Dot product and norms
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    return round(similarity * 100, 2)

# UI
st.header("📘 Upload or Paste Text")
col1, col2 = st.columns(2)

with col1:
    uploaded_file1 = st.file_uploader("Upload Original Document", type=["pdf", "docx", "txt"], key="file1")
    text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)

with col2:
    uploaded_file2 = st.file_uploader("Upload Submitted Document", type=["pdf", "docx", "txt"], key="file2")
    text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

# Threshold slider
st.markdown("---")
threshold = st.slider("Set plagiarism threshold (%)", min_value=10, max_value=100, value=50, step=5)

# Check plagiarism
if st.button("🔍 Check for Plagiarism"):
    if text1.strip() and text2.strip():
        similarity = compute_cosine_similarity(text1, text2)
        st.success(f"Cosine Similarity Score: **{similarity}%**")

        if similarity >= threshold:
            st.warning("⚠️ High similarity detected. This might be plagiarized.")
        else:
            st.info("✅ Low similarity. No plagiarism detected.")
    else:
        st.error("Both inputs are required.")
