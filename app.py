import streamlit as st

# Must be first
st.set_page_config(page_title="AI Plagiarism & Paraphrasing", layout="wide")

from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai

# Configure Gemini API
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-pro")

# Gemini paraphrasing
def paraphrase_text_gemini(text):
    try:
        prompt = f"Paraphrase the following text in clear academic English:\n\n{text}"
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Paraphrasing failed: {e}"

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
st.title("🧠 AI Plagiarism Checker & Paraphrasing Tool (Gemini-Powered)")

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
        if score > 50:
            st.warning("High similarity detected. Here's a paraphrased version:")
            st.subheader("💡 Paraphrased Text")
            st.write(paraphrase_text_gemini(text2))
    else:
        st.error("Both inputs required.")

# Paraphrasing Section
st.markdown("---")
st.header("✍️ Paraphrasing Tool")

user_input = st.text_area("Enter text to paraphrase using Gemini", height=200)
if st.button("♻️ Generate Paraphrased Text"):
    if user_input.strip():
        output = paraphrase_text_gemini(user_input)
        st.subheader("🔁 Paraphrased Output")
        st.write(output)
    else:
        st.warning("Please enter text to paraphrase.")
