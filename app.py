import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests
import base64
import time

# --- SETUP ---
st.set_page_config(page_title="Sigma AI | Plagiarism & Paraphrasing", layout="wide")

# 🔑 API Keys
GEMINI_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"
COPYSCOPE_API_TOKEN = "ylxcyl2671nstrxa"

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
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

# Simulated Copyscape check
def check_plagiarism_copyscape(text):
    try:
        encoded_text = base64.b64encode(text.encode()).decode()
        url = f"https://www.copyscape.com/api/?u={COPYSCOPE_API_TOKEN}&o=csearch&t={encoded_text}"
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": f"❌ Copyscape API Error: {response.status_code}"}
        
        if "<result>" in response.text:
            return {"report": {"matches_found": True, "content": response.text}}
        else:
            return {"report": {"matches_found": False, "content": "No matches found."}}
    except Exception as e:
        return {"error": f"❌ API request failed: {e}"}

# --- UI STARTS HERE ---
st.title("🧠 Sigma AI – Plagiarism & Paraphrasing Tool")

tabs = st.tabs(["🔍 Compare Files", "🌐 Check Online Plagiarism", "✍️ Paraphrasing"])

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

# --- Tab 2: Copyscape Plagiarism Check ---
with tabs[1]:
    st.header("🌐 Copyscape – Online Plagiarism Checker")
    file = st.file_uploader("Upload file", type=["pdf", "docx", "txt"], key="online_file")
    text = extract_text(file) if file else st.text_area("Or paste text to check", key="online_text")

    if st.button("🔎 Submit to Copyscape"):
        if text.strip():
            with st.spinner("Submitting text to Copyscape..."):
                result = check_plagiarism_copyscape(text)

            if "error" in result:
                st.error(result["error"])
            else:
                report = result["report"]
                if report["matches_found"]:
                    st.success("✅ Matches found:")
                    st.code(report["content"])
                else:
                    st.info("✅ No plagiarism detected.")
        else:
            st.error("Please upload or paste content.")

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
