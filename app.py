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

GOOGLE_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"
COPYLEAKS_EMAIL = "ahtisham.asghar1122@gmail.com"  
COPYLEAKS_API_KEY = "e7a9563c-3b50-4390-a329-20b2529beacb"  

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

        # Step 2: Submit content
        scan_id = f"scan-{datetime.utcnow().timestamp()}"
        scan_url = f"https://api.copyleaks.com/v3/scans/submit/{scan_id}"
        scan_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        scan_payload = {
            "base64": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
            "filename": "uploaded.txt",
            "properties": {
                "webhooks": {
                    "status": "https://webhook.site/your-temp-webhook"  # Optional
                }
            }
        }
        scan_resp = requests.put(scan_url, json=scan_payload, headers=scan_headers)
        if scan_resp.status_code not in [200, 201, 202]:
            return {"error": f"Scan submission failed: {scan_resp.text}"}

        return {"success": f"Plagiarism scan submitted. Please check results on Copyleaks dashboard. Scan ID: {scan_id}"}

    except Exception as e:
        return {"error": str(e)}


# --- UI Layout ---
st.title("🧠 AI Plagiarism Checker & Paraphrasing Tool")
tabs = st.tabs(["🔍 File Comparison", "🌐 Online Plagiarism Check", "✍️ Paraphrasing"])


# --- Tab 1: File vs File Comparison ---
with tabs[0]:
    st.header("📘 Plagiarism Checker (File-to-File)")
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader("Upload Original Text File", type=["pdf", "docx", "txt"], key="file1")
        text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)
    with col2:
        uploaded_file2 = st.file_uploader("Upload Submitted Text File", type=["pdf", "docx", "txt"], key="file2")
        text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

    threshold = st.slider("Set Similarity Threshold for Paraphrasing (%)", min_value=0, max_value=100, value=10, step=1)

    if st.button("🔍 Check for Plagiarism"):
        if text1.strip() and text2.strip():
            score = get_similarity(text1, text2)
            st.success(f"Similarity Score: **{score}%**")
            if score >= threshold:
                st.warning(f"Similarity exceeds threshold of {threshold}%. Generating paraphrased version:")
                st.subheader("💡 Paraphrased Text")
                st.write(paraphrase_text_gemini(text2))
            else:
                st.info(f"Similarity is below the threshold of {threshold}%. No paraphrasing needed.")
        else:
            st.error("Both inputs required.")


# --- Tab 2: Online Plagiarism Checker ---
with tabs[1]:
    st.header("🌐 Online Plagiarism Checker")
    uploaded_online = st.file_uploader("Upload Document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="online")
    online_text = extract_text_from_file(uploaded_online) if uploaded_online else st.text_area("Or paste text", height=250, key="online_text")

    if st.button("Check Online Plagiarism", key="online_check"):
        if online_text.strip():
            with st.spinner("Submitting content to Copyleaks..."):
                result = online_plagiarism_check(online_text)

            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["success"])
                st.info("📌 Results may take time. Please visit your Copyleaks dashboard to view the full report.")
        else:
            st.error("Please upload or paste text to check.")


# --- Tab 3: Paraphrasing Tool ---
with tabs[2]:
    st.header("✍️ Paraphrasing Tool")
    user_input = st.text_area("Enter text to paraphrase using Gemini", height=200)
    if st.button("♻️ Generate Paraphrased Text"):
        if user_input.strip():
            output = paraphrase_text_gemini(user_input)
            st.subheader("🔁 Paraphrased Output")
            st.write(output)
        else:
            st.warning("Please enter text to paraphrase.")
