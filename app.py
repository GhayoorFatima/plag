import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
import requests
from datetime import datetime
from fpdf import FPDF
import tempfile

# --- Configuration ---
st.set_page_config(page_title="Sigma AI Plagiarism & Paraphrasing", layout="wide")
GOOGLE_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"
WINSTON_API_KEY = "plB6Hp7MFW3xNjkr6IGE96BAf7ntQ9r12qj1FEWv92a78517"
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
    url = "https://api.gowinston.ai/v2/plagiarism"
    headers = {
        "Authorization": f"Bearer {WINSTON_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": text, "language": "en", "country": "us"}
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        return {"error": f"API Error: {resp.status_code} – {resp.text}"}
    return resp.json()

def generate_plagiarism_pdf(result, text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Sigma AI Plagiarism Report", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 8, f"Similarity Score: {result['result']['score']}%", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Matched Sources:", ln=True)
    pdf.set_font("Arial", size=11)
    for src in result.get("sources", []):
        pdf.multi_cell(0, 6,
            f"- URL: {src['url']}\n  Title: {src.get('title','N/A')}\n  Similarity: {src['score']}%\n  Snippet: {src['plagiarismFound'][0]['sequence'] if src.get('plagiarismFound') else ''}\n"
        )

    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Citations:", ln=True)
    pdf.set_font("Arial", size=11)
    for i, src in enumerate(result.get("sources", []), 1):
        pdf.cell(0, 6, f"[{i}] {src['url']}", ln=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

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
            with st.spinner("Checking online sources..."):
                result = online_plagiarism_check(online_text)

            if "error" in result:
                st.error(result["error"])
            else:
                score = result["result"]["score"]
                st.success(f"Similarity Score: **{score}%**")
                st.subheader("🔍 Matched Sources")
                for src in result.get("sources", []):
                    url = src["url"]
                    sim = src["score"]
                    snippet = src["plagiarismFound"][0]["sequence"] if src.get("plagiarismFound") else ""
                    st.markdown(f"- **URL:** [{url}]({url}) — {sim}% match")
                    if snippet:
                        st.markdown(f"  > Snippet: _{snippet}_")

                pdf_path = generate_plagiarism_pdf(result, online_text)
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Download PDF Report", f, file_name="Sigma_Plagiarism_Report.pdf")
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
