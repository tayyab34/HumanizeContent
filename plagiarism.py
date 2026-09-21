from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from web_search import search_web


def split_text(text, chunk_size=500):
    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunks.append(
            " ".join(words[i:i + chunk_size])
        )

    return chunks


def similarity_score(a, b):
    vectorizer = TfidfVectorizer()

    vectors = vectorizer.fit_transform([a, b])

    score = cosine_similarity(
        vectors[0:1],
        vectors[1:2]
    )[0][0]

    return round(score * 100, 2)


def check_plagiarism(document_text, similarity_threshold=70):

    chunks = split_text(document_text)

    results = []

    for chunk in chunks[:10]:

        query = " ".join(chunk.split()[:20])

        web_results = search_web(query)

        for item in web_results:

            score = similarity_score(
                chunk,
                item["snippet"]
            )

            if score >= similarity_threshold:

                results.append({
                    "similarity": score,
                    "url": item["url"],
                    "snippet": item["snippet"],
                    "matched_text": chunk[:500]
                })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results
