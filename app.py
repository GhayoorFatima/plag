import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests

# Must be first
st.set_page_config(page_title="AI Plagiarism & Paraphrasing", layout="wide")

# === Configuration ===
# Gemini API Key
GOOGLE_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Online Plagiarism Checker API Key
PLAGIARISM_API_KEY = "wx2ITlcQhCPh5fmOFiochTyUP0pjoXsifZbhgst837818ca4"

# === Functions ===

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
        headers = {
            "Authorization": f"Bearer {PLAGIARISM_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": text
        }

        # Replace with your actual API endpoint if different
        response = requests.post("https://api.plagiarismchecker.ai/v1/check", json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return {
                "percentage": data.get("plagiarism", 0.0),
                "sources": data.get("matches", [])
            }
        else:
            return {
                "percentage": 0.0,
                "sources": [],
                "error": f"API Error: {response.status_code} - {response.text}"
            }

    except Exception as e:
        return {
            "percentage": 0.0,
            "sources": [],
            "error": str(e)
        }

# === UI ===
st.title("🧠 AI Plagiarism Checker & Paraphrasing Tool")

tab1, tab2, tab3 = st.tabs(["🔍 Local Plagiarism Checker", "🌐 Online Plagiarism Checker", "✍️ Paraphrasing Tool"])

# --- Tab 1: Local File-to-File Checker ---
with tab1:
    st.header("🔍 Local File-to-File Plagiarism Checker")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file1 = st.file_uploader("Upload Original Text File", type=["pdf", "docx", "txt"], key="file1")
        text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)

    with col2:
        uploaded_file2 = st.file_uploader("Upload Submitted Text File", type=["pdf", "docx", "txt"], key="file2")
        text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

    threshold = st.slider("Set Similarity Threshold for Paraphrasing (%)", 0, 100, 10, 1)

    if st.button("Check for Plagiarism (Local)", key="local_check"):
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
            st.error("Both inputs are required.")

# --- Tab 2: Online Checker ---
with tab2:
    st.header("🌐 Online Plagiarism Checker (Web Sources)")

    uploaded_online = st.file_uploader("Upload File to Check Online", type=["pdf", "docx", "txt"], key="online_file")
    online_text = extract_text_from_file(uploaded_online) if uploaded_online else st.text_area("Or paste text to check online", height=250)

    if st.button("Check Online Plagiarism", key="online_check"):
        if online_text.strip():
            with st.spinner("Checking online sources..."):
                result = online_plagiarism_check(online_text)

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"Estimated Online Plagiarism: **{result['percentage']}%**")
                st.subheader("🔗 Matched Sources")
                for match in result["sources"]:
                    st.markdown(f"- **Source:** [{match['source']}]({match['source']})\n\n  > Matched Text: _{match['matched']}_")
        else:
            st.error("Please provide text or upload a document.")

# --- Tab 3: Paraphrasing Tool ---
with tab3:
    st.header("✍️ Paraphrasing Tool")
    user_input = st.text_area("Enter text to paraphrase using Gemini", height=200)

    if st.button("♻️ Generate Paraphrased Text", key="paraphrase"):
        if user_input.strip():
            output = paraphrase_text_gemini(user_input)
            st.subheader("🔁 Paraphrased Output")
            st.write(output)
        else:
            st.warning("Please enter text to paraphrase.")
