import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests
from datetime import datetime
import base64
import time

# --- Configuration ---
st.set_page_config(page_title="Sigma AI Plagiarism & Paraphrasing", layout="wide")

# 🔑 Set your API keys here directly
GOOGLE_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"
PLAGCHECK_API_TOKEN = "kvcZ7jnVWANxAZOVuZZvxF83V8D6QmWw"

# Gemini Model Setup
genai.configure(api_key=GOOGLE_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

# --- Utility Functions ---
def paraphrase_gemini(text):
    prompt = f"Paraphrase the following text in clear academic English:\n\n{text}"
    try:
        return gemini.generate_content(prompt).text.strip()
    except Exception as e:
        return f"⚠️ Paraphrasing error: {e}"

def similarity(a, b):
    return round(SequenceMatcher(None, a, b).ratio() * 100, 2)

def extract_text(file):
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif file.name.endswith(".docx"):
        return "\n".join(p.text for p in docx.Document(file).paragraphs)
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    return ""

# --- PlagiarismCheck.org Integration ---
def check_plagiarism(text):
    headers = {"Authorization": f"Bearer {PLAGCHECK_API_TOKEN}"}
    
    # Step 1: Submit
    submit = requests.post("https://plagiarismcheck.org/api/v1/text", headers=headers, json={"text": text})
    if submit.status_code != 200:
        return {"error": f"Submit failed: {submit.status_code} — {submit.text}"}
    
    job_id = submit.json().get("id")

    # Step 2: Poll for completion
    for _ in range(10):
        time.sleep(2)
        status = requests.get(f"https://plagiarismcheck.org/api/v1/text/{job_id}", headers=headers)
        if status.status_code != 200:
            return {"error": f"Status failed: {status.status_code}"}
        result = status.json()
        if not result.get("checking", True):
            return {"report": result}
    
    return {"error": "⏳ Timeout waiting for scan to complete."}

# --- UI Layout ---
st.title("🧠 Sigma AI: Plagiarism & Paraphrasing Tool")
tabs = st.tabs(["🔍 File Comparison", "🌐 Online Plagiarism Check", "✍️ Paraphrasing"])

# --- Tab 1: File-to-File Comparison ---
with tabs[0]:
    st.header("📘 File-to-File Comparison")
    col1, col2 = st.columns(2)
    file1 = st.file_uploader("Upload Original File", type=["pdf", "docx", "txt"], key="file1")
    file2 = st.file_uploader("Upload Submitted File", type=["pdf", "docx", "txt"], key="file2")
    text1 = extract_text(file1) if file1 else st.text_area("Or paste original text", height=250)
    text2 = extract_text(file2) if file2 else st.text_area("Or paste submitted text", height=250)

    threshold = st.slider("Similarity Threshold (%)", 0, 100, 10)

    if st.button("🔍 Compare Texts"):
        if text1.strip() and text2.strip():
            score = similarity(text1, text2)
            st.success(f"Similarity Score: **{score}%**")
            if score >= threshold:
                st.warning(f"⚠️ Similarity exceeds {threshold}%. Paraphrasing suggestion below:")
                st.write(paraphrase_gemini(text2))
            else:
                st.info("Similarity is below threshold. No paraphrasing needed.")
        else:
            st.error("Please provide both texts.")

# --- Tab 2: Online Plagiarism Check ---
with tabs[1]:
    st.header("🌐 Online Plagiarism Check via PlagiarismCheck.org")
    file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"], key="plag")
    input_text = extract_text(file) if file else st.text_area("Or paste text", height=250)

    if st.button("🔎 Submit to PlagiarismCheck.org"):
        if input_text.strip():
            with st.spinner("Submitting for plagiarism scan..."):
                response = check_plagiarism(input_text)

            if "error" in response:
                st.error(response["error"])
            else:
                report = response["report"]
                st.success(f"✅ Similarity: {report.get('plagPercent', 0)}%")
                st.markdown("### 🔗 Sources Found:")
                for d in report.get("details", []):
                    for w in d.get("webs", []):
                        st.markdown(f"- [{w['title']}]({w['url']})")
                        st.markdown(f"  > {d['query']}")
        else:
            st.error("Please upload or paste text.")

# --- Tab 3: Paraphrasing Tool ---
with tabs[2]:
    st.header("✍️ Paraphrasing Using Gemini")
    user_text = st.text_area("Enter text to paraphrase", height=200)
    if st.button("♻️ Paraphrase Now"):
        if user_text.strip():
            result = paraphrase_gemini(user_text)
            st.subheader("🔁 Paraphrased Output")
            st.write(result)
        else:
            st.warning("Enter text to paraphrase.")
