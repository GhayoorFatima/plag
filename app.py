import streamlit as st
from similarity import get_similarity
from paraphraser import paraphrase_text

st.set_page_config(page_title="AI Plagiarism Checker", layout="wide")

st.title("🧠 AI-Enhanced Plagiarism Checker")
st.markdown("Compare texts, detect plagiarism, and get paraphrasing suggestions.")

col1, col2 = st.columns(2)

with col1:
    text1 = st.text_area("Original / Source Text", height=250)
with col2:
    text2 = st.text_area("Student Submission", height=250)

if st.button("🔍 Check for Plagiarism"):
    if text1.strip() and text2.strip():
        similarity = get_similarity(text1, text2)
        st.success(f"Similarity Score: **{similarity}%**")

        if similarity > 50:
            st.warning("High similarity detected. Generating paraphrased suggestions...")
            st.subheader("💡 Paraphrased Text")
            st.write(paraphrase_text(text2))
    else:
        st.error("Please enter both texts before checking.")