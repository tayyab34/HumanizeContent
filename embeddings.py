from sklearn.feature_extraction.text import TfidfVectorizer

def create_faiss_index(texts):
    vectorizer = TfidfVectorizer(stop_words="english")

    if isinstance(texts, str):
        texts = [texts]

    vectors = vectorizer.fit_transform(texts)

    return vectorizer, vectors
