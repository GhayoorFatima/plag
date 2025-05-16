import streamlit as st
from PyPDF2 import PdfReader
import docx
from difflib import SequenceMatcher

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Load paraphrasing model (t5-small)
@st.cache_resource
def load_paraphraser():
    model_name = "t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return pipeline("text2text-generation", model=model, tokenizer=tokenizer)

paraphraser = load_paraphraser()

# Paraphrasing function
def paraphrase_text(text):
    if not text.strip():
        return "⚠️ Please enter valid text to paraphrase."
    try:
        input_text = "paraphrase: " + text + " </s>"
        result = paraphraser(input_text, max_length=60, num_return_sequences=1, do_sample=True)
        return result[0]['generated_text']
    except Exception as e:
        return f"⚠️ Paraphrasing failed: {str(e)}"

# Similarity checker
def get_similarity(text1, text2):
    return round(SequenceMatcher(None, text1, text2).ratio() * 100, 2)

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

# Streamlit UI
st.set_page_config(page_title="AI Plagiarism & Paraphrasing", layout="wide")
st.title("🧠 AI Plagiarism Checker & Paraphrasing Tool")

st.markdown("Upload files or paste text to check for plagiarism or paraphrase content.")

# Input Section
st.header("📘 Plagiarism Checker")
col1, col2 = st.columns(2)

with col1:
    uploaded_file1 = st.file_uploader("Upload Original Text File", type=["pdf", "docx", "txt"], key="file1")
    text1 = extract_text_from_file(uploaded_file1) if uploaded_file1 else st.text_area("Or paste Original Text", height=250)

with col2:
    uploaded_file2 = st.file_uploader("Upload Submitted Text File", type=["pdf", "docx", "txt"], key="file2")
    text2 = extract_text_from_file(uploaded_file2) if uploaded_file2 else st.text_area("Or paste Submitted Text", height=250)

if st.button("🔍 Check for Plagiarism"):
    if text1.strip() and text2.strip():
        score = get_similarity(text1, text2)
        st.success(f"Similarity Score: **{score}%**")
        if score > 50:
            st.warning("High similarity detected. Here's a paraphrased version:")
            st.write(paraphrase_text(text2))
    else:
        st.error("Both text inputs are required to check for plagiarism.")

# Paraphrasing Section
st.markdown("---")
st.header("✍️ Paraphrasing Tool")

text_to_paraphrase = st.text_area("Enter text to paraphrase", height=200)
if st.button("♻️ Generate Paraphrased Text"):
    output = paraphrase_text(text_to_paraphrase)
    st.subheader("🔁 Paraphrased Output")
    st.write(output)
