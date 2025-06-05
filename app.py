import streamlit as st
from PyPDF2 import PdfReader
import docx
import google.generativeai as genai

# ✅ Set page config first!
st.set_page_config(page_title="AI Plagiarism & Paraphrasing", layout="wide")

# ✅ Gemini API setup
GOOGLE_API_KEY = "AIzaSyCOzTWV41mYCfOva_NBI2if_M8XlKD6gOA"  # Replace with your actual key or use secrets
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ✅ Function to read text from supported document formats
def read_text_from_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == "pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif file_type == "txt":
        return uploaded_file.read().decode("utf-8")
    elif file_type == "docx":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return None

# ✅ Function to get Gemini response
def get_gemini_response(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ✅ Streamlit UI
st.title("📄 AI-Enhanced Plagiarism Checker with Paraphrasing Support")

uploaded_file = st.file_uploader("Upload a document (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])

if uploaded_file:
    document_text = read_text_from_file(uploaded_file)

    if document_text:
        st.subheader("Extracted Text")
        st.text_area("Original Document Text", document_text, height=300)

        # Paraphrasing
        if st.button("Paraphrase Text"):
            with st.spinner("Paraphrasing using Gemini..."):
                prompt = f"Paraphrase the following text in a human-like way:\n\n{document_text}"
                paraphrased_text = get_gemini_response(prompt)
                st.subheader("Paraphrased Text")
                st.text_area("AI-Paraphrased Text", paraphrased_text, height=300)
    else:
        st.error("Unsupported file type or failed to extract text.")
