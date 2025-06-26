import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests
from datetime import datetime
from fpdf import FPDF
import tempfile
import time

# --- Configuration ---
st.set_page_config(page_title="Sigma AI Plagiarism & Paraphrasing", layout="wide")

GOOGLE_API_KEY = st.secrets["AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"] 
PC_API_TOKEN = st.secrets["kvcZ7jnVWANxAZOVuZZvxF83V8D6QmWw"]  

genai.configure(api_key=GOOGLE_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

# --- Utility Functions ---
def paraphrase_gemini(text):
    prompt = f"Paraphrase in clear academic English:\n\n{text}"
    try:
        return gemini.generate_content(prompt).text.strip()
    except Exception as e:
        return f"⚠️ Paraphrasing error: {e}"

def similarity(a, b):
    return round(SequenceMatcher(None, a, b).ratio() * 100, 2)

def extract_text(uploaded):
    if uploaded.name.endswith(".pdf"):
        return "\n".join(PdfReader(uploaded).pages[i].extract_text()
                         for i in range(len(PdfReader(uploaded).pages))
                         if PdfReader(uploaded).pages[i].extract_text())
    if uploaded.name.endswith(".docx"):
        return "\n".join(p.text for p in docx.Document(uploaded).paragraphs)
    if uploaded.name.endswith(".txt"):
        return uploaded.read().decode("utf-8")
    return ""

# --- PlagiarismCheck.org Integration ---
def check_plagiarism(text):
    # Step 1: Submit
    headers = {"Authorization": f"Bearer {PC_API_TOKEN}"}
    r = requests.post("https://plagiarismcheck.org/api/v1/text", headers=headers, json={"text": text})
    if r.status_code != 200:
        return {"error": f"Submit failed: {r.status_code} — {r.text}"}
    jid = r.json().get("id")
    # Step 2: Poll status
    for _ in range(10):
        time.sleep(2)
        q = requests.get(f"https://plagiarismcheck.org/api/v1/text/{jid}", headers=headers)
        if q.status_code != 200:
            return {"error": f"Status failed: {q.status_code}"}
        d = q.json()
        if not d.get("checking"):
            return {"report": d}
    return {"error": "Timed out waiting for check"}

# --- UI Layout ---
st.title("🧠 Sigma AI: Plagiarism Checker & Paraphrasing")

tabs = st.tabs(["File Comparison", "Online Check", "Paraphrasing"])

with tabs[0]:
    st.header("📘 File-to-File Comparison")
    c1, c2 = st.columns(2)
    f1 = st.file_uploader("Original", ["pdf","docx","txt"], key="f1")
    f2 = st.file_uploader("Submitted", ["pdf","docx","txt"], key="f2")
    t1 = extract_text(f1) if f1 else st.text_area("Paste original")
    t2 = extract_text(f2) if f2 else st.text_area("Paste submitted")
    th = st.slider("Threshold (%)", 0, 100, 10)
    if st.button("Compare"):
        if t1 and t2:
            sc = similarity(t1, t2)
            st.success(f"Similarity: {sc}%")
            if sc >= th:
                st.warning("⚠️ Exceeds threshold — paraphrasing below:")
                st.write(paraphrase_gemini(t2))
        else:
            st.error("Both texts are required.")

with tabs[1]:
    st.header("🌐 Online PlagiarismCheck.org Check")
    f = st.file_uploader("Upload document", ["pdf","docx","txt"], key="online")
    txt = extract_text(f) if f else st.text_area("Or paste text", height=250)
    if st.button("Check Now"):
        if txt.strip():
            with st.spinner("Checking plagiarism..."):
                res = check_plagiarism(txt)
            if "error" in res:
                st.error(res["error"])
            else:
                rpt = res["report"]
                st.success(f"✅ Checked — Similarity: {rpt.get('plagPercent')}%")
                st.markdown("**Matches:**")
                for d in rpt.get("details", []):
                    for w in d.get("webs", []):
                        st.markdown(f"- [{w['title']}]({w['url']})")
                        st.markdown(f"  > {d['query']}")
        else:
            st.error("Please upload or enter text.")

with tabs[2]:
    st.header("✍️ Paraphrase with Gemini")
    inp = st.text_area("Enter text", height=200)
    if st.button("Paraphrase"):
        if inp:
            st.write(paraphrase_gemini(inp))
        else:
            st.warning("Enter text first.")
