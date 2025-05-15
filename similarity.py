from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit([text1, text2])
    tfidf = vectorizer.transform([text1, text2])
    similarity_score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(similarity_score * 100, 2)