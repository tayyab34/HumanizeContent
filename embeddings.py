import faiss
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer


def create_faiss_index(texts):

    if not texts:
        return None, None

    cleaned_texts = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not cleaned_texts:
        return None, None

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=10000
    )

    matrix = vectorizer.fit_transform(
        cleaned_texts
    )

    vectors = matrix.astype(
        np.float32
    ).toarray()

    index = faiss.IndexFlatIP(
        vectors.shape[1]
    )

    faiss.normalize_L2(vectors)

    index.add(vectors)

    return index, vectorizer


def search_similar(
    query,
    texts,
    index,
    vectorizer,
    top_k=5
):

    if (
        not query
        or not texts
        or index is None
        or vectorizer is None
    ):
        return []

    query_vector = vectorizer.transform(
        [query]
    ).astype(
        np.float32
    ).toarray()

    faiss.normalize_L2(
        query_vector
    )

    scores, indices = index.search(
        query_vector,
        min(top_k, index.ntotal)
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:
            continue

        results.append({
            "text": texts[idx],
            "score": float(score)
        })

    return results
