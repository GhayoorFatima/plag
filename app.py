import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests
from datetime import datetime
from fpdf import FPDF
import tempfile
import base64

# --- Configuration ---
st.set_page_config(page_title="Sigma AI Plagiarism & Paraphrasing", layout="wide")

GOOGLE_API_KEY = "your_gemini_api_key_here"
COPYLEAKS_EMAIL = "your_email@domain.com"
COPYLEAKS_API_KEY = "your_copyleaks_api_key_here"

genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# --- Functions ---
def paraphrase_text_gemini(text):
    try:
        prompt = f"Paraphrase the following text in clear academic English:\n\n{text}"
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Paraphrasing failed: {e}"

def get_similarity(text1, text2):
    return round(SequenceMatcher(None, text1, text2).ratio() * 100, 2)

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

def online_plagiarism_check(text):
    try:
        # Step 1: Authenticate
        auth_url = "https://id.copyleaks.com/v3/account/login/api"
        auth_payload = {"email": COPYLEAKS_EMAIL, "key": COPYLEAKS_API_KEY}
        auth_resp = requests.post(auth_url, json=auth_payload)
        if auth_resp.status_code != 200:
            return {"error": f"Authentication Failed: {auth_resp.text}"}
        access_token = auth_resp.json()["access_token"]

        # Step 2: Prepare scan
        scan_id = f"scan-{datetime.utcnow().timestamp()}"
        scan_url = f"https://api.copyleaks.com/v3/scans/submit/{scan_id}"
        scan_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        base64_content = base64.b64encode(text.encode("utf-8")).decode("utf-8")

        scan_payload = {
            "base64": base64_content,
            "filename": "uploaded.txt"
        }

        # Step 3: Submit scan
        scan_resp = requests.put(scan_url, json=scan_payload, headers=scan_headers)
        if scan_resp.status_code not in [200, 201, 202]:
            return {"error": f"Scan submission failed: {scan_resp.status_code} — {scan_resp.text}"}

        return {"success": f"✅ Scan submitted successfully. Please check your Copyleaks dashboard.\nScan ID: {scan_id}"}

    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

# --- UI Layout ---
st.title("🧠 Sigma AI: Plagiarism Checker & Paraphrasing Tool")
tabs = st.tabs(["🔍 File Comparison", "🌐 Online Plagiarism Check", "✍️ Paraphrasing"])

# --- Tab 1: File-to-File Comparison ---
with tabs[0]:
    st.header("📘 File-to-File Plagiarism Check")
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader("Upload Original File", type=["pdf", "docx", "txt"], key="file1")
        text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste original text", height=250)
    with col2:
        uploaded_file2 = st.file_uploader("Upload Submitted File", type=["pdf", "docx", "txt"], key="file2")
        text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste submitted text", height=250)

    threshold = st.slider("Similarity Threshold (%)", 0, 100, 10)

    if st.button("🔍 Check Similarity"):
        if text1.strip() and text2.strip():
            score = get_similarity(text1, text2)
            st.success(f"Similarity Score: **{score}%**")
            if score >= threshold:
                st.warning(f"⚠️ Similarity exceeds threshold of {threshold}%.")
                st.subheader("💡 Suggested Paraphrased Version:")
                st.write(paraphrase_text_gemini(text2))
            else:
                st.info("Similarity below threshold. No paraphrasing needed.")
        else:
            st.error("Please provide both texts.")

# --- Tab 2: Online Plagiarism Check ---
with tabs[1]:
    st.header("🌐 Copyleaks Online Plagiarism Check")
    uploaded_online = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"], key="online")
    online_text = extract_text_from_file(uploaded_online) if uploaded_online else st.text_area("Or paste text", height=250)

    if st.button("🔎 Submit to Copyleaks"):
        if online_text.strip():
            with st.spinner("Submitting to Copyleaks..."):
                result = online_plagiarism_check(online_text)

            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["success"])
                st.info("ℹ️ Results will appear in your Copyleaks dashboard.")
        else:
            st.error("Please enter or upload some text.")

# --- Tab 3: Paraphrasing Tool ---
with tabs[2]:
    st.header("✍️ Paraphrasing with Gemini")
    user_input = st.text_area("Enter text to paraphrase", height=200)
    if st.button("♻️ Paraphrase Now"):
        if user_input.strip():
            output = paraphrase_text_gemini(user_input)
            st.subheader("🔁 Paraphrased Output")
            st.write(output)
        else:
            st.warning("Please enter some text to paraphrase.")
