import streamlit as st
from PyPDF2 import PdfReader
import docx
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# Load lightweight paraphrasing model
try:
    MODEL_NAME = "t5-small"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    paraphraser = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

    def paraphrase_text(text):
        input_text = "paraphrase: " + text + " </s>"
        try:
            result = paraphraser(input_text, max_length=60, num_return_sequences=1, do_sample=True)
            return result[0]['generated_text']
        except Exception as e:
            return f"⚠️ Paraphrasing failed: {str(e)}"

except Exception as e:
    paraphraser = None

    def paraphrase_text(text):
        return "⚠️ Could not load paraphrasing model. Try again later."

# Simple similarity checker
from difflib import SequenceMatcher
def get_similarity(text1, text2):
    return round(SequenceMatcher(None, text1, text2).ratio() * 100, 2)

# Streamlit app UI
st.set_page_config(page_title="AI Plagiarism Checker", layout="wide")
st.title("🧠 AI-Enhanced Plagiarism Checker")
st.markdown("Compare texts, detect plagiarism, and get paraphrasing suggestions.")

# File text extraction
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        return "⚠️ Unsupported file format. Please upload a PDF, DOCX, or TXT file."

# Input columns
st.header("📘 Plagiarism Checker")
col1, col2 = st.columns(2)

with col1:
    uploaded_file1 = st.file_uploader("Upload Original / Source File", type=["pdf", "docx", "txt"], key="file1")
    if uploaded_file1:
        text1 = extract_text_from_file(uploaded_file1)
    else:
        text1 = st.text_area("Or paste Original / Source Text", height=250)

with col2:
    uploaded_file2 = st.file_uploader("Upload Student Submission File", type=["pdf", "docx", "txt"], key="file2")
    if uploaded_file2:
        text2 = extract_text_from_file(uploaded_file2)
    else:
        text2 = st.text_area("Or paste Student Submission Text", height=250)

# Plagiarism Check
if st.button("🔍 Check for Plagiarism"):
    if text1.strip() and text2.strip():
        similarity = get_similarity(text1, text2)
        st.success(f"Similarity Score: **{similarity}%**")

        if similarity > 50:
            st.warning("High similarity detected. Generating paraphrased suggestions...")
            st.subheader("💡 Paraphrased Text")
            st.write(paraphrase_text(text2))
    else:
        st.error("Please enter or upload both texts before checking.")

# Paraphrasing tool
st.markdown("---")
st.header("✍️ Paraphrasing Tool")

text_to_paraphrase = st.text_area("Enter text to paraphrase", height=200)
if st.button("♻️ Generate Paraphrased Text"):
    if text_to_paraphrase.strip():
        st.subheader("🔁 Paraphrased Output")
        st.write(paraphrase_text(text_to_paraphrase))
    else:
        st.warning("Please enter some text to paraphrase.")
