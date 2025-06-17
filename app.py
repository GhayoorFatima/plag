import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher
import google.generativeai as genai
from fpdf import FPDF
import json
import re
import base64
import tempfile

# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"  # Replace with your actual key
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="AI Plagiarism & Paraphrasing", layout="wide")

# ===========================
# 📌 Helper Functions
# ===========================

def paraphrase_text_gemini(text):
    try:
        prompt = f"Paraphrase the following text in clear academic English:\n\n{text}"
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Paraphrasing failed: {e}"

def check_plagiarism_online(text):
    try:
        prompt = f"""
You are a plagiarism detection engine. Analyze the following text against known online sources. Respond in this JSON format:

{{
  "similarity_percentage": <number>,
  "sources": [
    {{
      "source_url": "<source URL or name>",
      "matched_lines": [
        "matched sentence 1",
        "matched sentence 2"
      ]
    }}
  ]
}}

Text:
{text}
"""
        response = gemini_model.generate_content(prompt)
        json_match = re.search(r'\{[\s\S]*\}', response.text)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"error": "❌ Could not parse structured result from Gemini."}
    except Exception as e:
        return {"error": f"⚠️ Online plagiarism check failed: {e}"}

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

# Generate downloadable plagiarism report as PDF
def generate_plagiarism_pdf(result, original_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="AI Plagiarism Detection Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Similarity Score: {result['similarity_percentage']}%", ln=True)

    if result.get("sources"):
        for idx, source in enumerate(result["sources"], 1):
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, txt=f"{idx}. Source: {source['source_url']}", ln=True)
            pdf.set_font("Arial", "", 11)
            for line in source["matched_lines"]:
                pdf.multi_cell(0, 10, f"- {line}")
    else:
        pdf.ln(10)
        pdf.cell(200, 10, txt="✅ No significant matches found online.", ln=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

def get_download_link(file_path, label="📄 Download Report"):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="plagiarism_report.pdf">{label}</a>'

# ===========================
# 🎯 App UI
# ===========================

st.title("🧠 AI Plagiarism Checker & Paraphrasing Tool")
tab1, tab2 = st.tabs(["🔍 Plagiarism Checker", "✍️ Paraphrasing Tool"])

# ===========================
# 🔍 TAB 1: Plagiarism Checker
# ===========================
with tab1:
    st.header("📘 Document Comparison")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader("Upload Original Text File", type=["pdf", "docx", "txt"], key="file1")
        text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)

    with col2:
        uploaded_file2 = st.file_uploader("Upload Submitted Text File", type=["pdf", "docx", "txt"], key="file2")
        text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

    threshold = st.slider("Set Similarity Threshold (%)", min_value=0, max_value=100, value=10, step=1)

    if st.button("🔍 Check for Plagiarism"):
        if text1.strip() and text2.strip():
            score = get_similarity(text1, text2)
            st.success(f"🧪 Similarity Score: **{score}%**")

            if score >= threshold:
                st.warning(f"Similarity exceeds threshold of {threshold}%. Generating paraphrased version:")
                st.subheader("💡 Paraphrased Text")
                st.write(paraphrase_text_gemini(text2))
            else:
                st.info(f"Similarity is below the threshold of {threshold}%. No paraphrasing needed.")
        else:
            st.error("❌ Both text inputs are required.")

    st.markdown("---")
    st.header("🌐 Online Plagiarism Check")

    online_file = st.file_uploader("Upload File to Check Against Online Sources", type=["pdf", "docx", "txt"], key="online_file")
    online_text = extract_text_from_file(online_file) if online_file else st.text_area("Or paste text manually to check", height=200)

    if st.button("🌍 Check Online Plagiarism"):
        if online_text.strip():
            result = check_plagiarism_online(online_text)

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader(f"🔎 Similarity Score: **{result['similarity_percentage']}%**")

                if result["sources"]:
                    st.subheader("🌍 Matched Sources & Lines")
                    for idx, source in enumerate(result["sources"], 1):
                        st.markdown(f"**{idx}. Source:** {source['source_url']}")
                        for line in source["matched_lines"]:
                            st.markdown(f"- _{line}_")
                else:
                    st.success("✅ No significant matches found online.")

                report_path = generate_plagiarism_pdf(result, online_text)
                st.markdown(get_download_link(report_path), unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please upload a file or enter some text.")

# ===========================
# ✍️ TAB 2: Paraphrasing Tool
# ===========================
with tab2:
    st.header("🔁 Gemini Paraphrasing Tool")
    user_input = st.text_area("Enter text to paraphrase", height=250)

    if st.button("♻️ Generate Paraphrased Text"):
        if user_input.strip():
            paraphrased = paraphrase_text_gemini(user_input)
            st.subheader("✍️ Paraphrased Output")
            st.write(paraphrased)
        else:
            st.warning("⚠️ Please enter text to paraphrase.")
