import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests
import base64
import time
import uuid

# --- SETUP ---
st.set_page_config(page_title="Sigma AI | Plagiarism & Paraphrasing", layout="wide")

# 🔑 API Keys
GEMINI_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"
COPYLEAKS_EMAIL = "your_email@example.com"  # Replace this
COPYLEAKS_API_KEY = "your_copyleaks_api_key"  # Replace this

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

# --- Copyleaks Integration ---
def get_copyleaks_token(email, api_key):
    url = "https://id.copyleaks.com/v3/account/login/api"
    payload = {
        "email": email,
        "key": api_key
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def submit_text_to_copyleaks(access_token, text):
    scan_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "base64": base64.b64encode(text.encode()).decode(),
        "properties": {
            "includeHtml": False,
            "sandbox": True  # Optional: Remove in production
        }
    }
    url = f"https://api.copyleaks.com/v3/scans/submit/{scan_id}"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return scan_id

def get_copyleaks_result(access_token, scan_id):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://api.copyleaks.com/v3/scans/{scan_id}/result"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return None  # Still processing
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

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

# --- Tab 2: Copyleaks Plagiarism Check ---
with tabs[1]:
    st.header("🌐 Copyleaks – Online Plagiarism Checker")
    file = st.file_uploader("Upload file", type=["pdf", "docx", "txt"], key="online_file")
    text = extract_text(file) if file else st.text_area("Or paste text to check", key="online_text")

    if st.button("🔎 Submit to Copyleaks"):
        if text.strip():
            with st.spinner("🔐 Authenticating and submitting..."):
                try:
                    token = get_copyleaks_token(COPYLEAKS_EMAIL, COPYLEAKS_API_KEY)
                    scan_id = submit_text_to_copyleaks(token, text)
                    st.success("✅ Submitted successfully! Waiting for scan results...")
                    time.sleep(10)

                    result = get_copyleaks_result(token, scan_id)
                    if result:
                        st.subheader("📋 Plagiarism Report")
                        for res in result:
                            st.write(f"🔗 Match Found: {res.get('url', 'N/A')}")
                            st.write(f"🧠 Score: {res.get('score', 0)}%")
                    else:
                        st.info("⏳ Scan is still processing. Please try again shortly.")

                except Exception as e:
                    st.error(f"❌ Error: {e}")
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
