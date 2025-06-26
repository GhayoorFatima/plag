import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai

# --- SETUP ---
st.set_page_config(page_title="Sigma AI | Plagiarism & Paraphrasing", layout="wide")

# 🔑 API Key for Gemini
genai.configure(api_key="AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA")
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# --- FUNCTIONS ---
def paraphrase_text(text):
    try:
        prompt = f"Paraphrase the following in clear academic English:\n\n{text}"
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Paraphrasing failed: {e}"

def get_similarity(text1, text2):
    return round(SequenceMatcher(None, text1, text2).ratio() * 100, 2)

def extract_text(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif uploaded_file.name.endswith(".docx"):
        return "\n".join(p.text for p in docx.Document(uploaded_file).paragraphs)
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        return ""

def ai_plagiarism_check(text):
    try:
        prompt = f"Analyze the following text and tell me if it appears to be plagiarized from known online content. Be honest and detailed.\n\n{text}"
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ AI plagiarism analysis failed: {e}"

# --- UI STARTS HERE ---
st.title("🧠 Sigma AI – Plagiarism & Paraphrasing Tool")

tabs = st.tabs(["🔍 Compare Files", "🌐 AI Online Plagiarism Check", "✍️ Paraphrasing"])

# --- Tab 1: File-to-File Similarity ---
with tabs[0]:
    st.header("📘 File-to-File Similarity Checker")
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("Upload Original Document", type=["pdf", "docx", "txt"], key="file1")
        text1 = extract_text(file1) if file1 else st.text_area("Or paste original text")
    with col2:
        file2 = st.file_uploader("Upload Submitted Document", type=["pdf", "docx", "txt"], key="file2")
        text2 = extract_text(file2) if file2 else st.text_area("Or paste submitted text")

    threshold = st.slider("Paraphrasing Threshold (%)", 0, 100, 10)

    if st.button("🔍 Check Similarity"):
        if text1.strip() and text2.strip():
            score = get_similarity(text1, text2)
            st.success(f"✅ Similarity Score: {score}%")
            if score >= threshold:
                st.warning("⚠️ Similarity exceeds threshold. Suggested paraphrasing:")
                st.write(paraphrase_text(text2))
            else:
                st.info("✅ No paraphrasing needed.")
        else:
            st.error("⚠️ Both texts are required.")

# --- Tab 2: AI-Based Online Plagiarism Check ---
with tabs[1]:
    st.header("🌐 AI-Based Online Plagiarism Check (via Gemini)")
    file = st.file_uploader("Upload file", type=["pdf", "docx", "txt"], key="ai_file")
    text = extract_text(file) if file else st.text_area("Or paste text to check", key="ai_text")

    if st.button("🧠 Check via AI"):
        if text.strip():
            with st.spinner("Analyzing with Gemini AI..."):
                result = ai_plagiarism_check(text)
                st.subheader("🧾 AI Analysis Result")
                st.write(result)
        else:
            st.error("⚠️ Please upload or paste content.")

# --- Tab 3: Paraphrasing Tool ---
with tabs[2]:
    st.header("✍️ AI Paraphrasing via Gemini")
    user_input = st.text_area("Enter text to paraphrase", height=200)
    if st.button("♻️ Paraphrase Now"):
        if user_input.strip():
            output = paraphrase_text(user_input)
            st.subheader("🔁 Paraphrased Output")
            st.write(output)
        else:
            st.warning("Please enter text.")
