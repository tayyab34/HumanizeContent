import os
import re
import requests
import streamlit as st

from embeddings import create_faiss_index, search_similar


def get_serpapi_key():
    """
    Get SERP API key from Streamlit secrets or environment variables.
    """

    try:
        key = st.secrets.get("SERPAPI_KEY", "")
    except Exception:
        key = ""

    if not key:
        key = os.getenv("SERPAPI_KEY", "")

    return key


def clean_text(text):
    """
    Clean text before searching.
    """

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def split_into_chunks(
    text,
    chunk_size=500,
    overlap=100
):
    """
    Split document into smaller chunks.
    """

    text = clean_text(text)

    if not text:
        return []

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = min(
            start + chunk_size,
            len(words)
        )

        chunk = " ".join(
            words[start:end]
        )

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def search_web(query, api_key, num_results=5):
    """
    Search Google through SERP API.
    """

    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results
    }

    try:

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "organic_results",
            []
        )

    except requests.RequestException:
        return []

    except ValueError:
        return []


def calculate_similarity(
    query,
    source_text
):
    """
    Calculate TF-IDF cosine similarity.
    """

    if not query or not source_text:
        return 0.0

    try:

        index, vectorizer = create_faiss_index(
            [source_text]
        )

        if index is None:
            return 0.0

        matches = search_similar(
            query,
            [source_text],
            index,
            vectorizer,
            top_k=1
        )

        if not matches:
            return 0.0

        score = matches[0]["score"]

        score = max(
            0.0,
            min(
                1.0,
                score
            )
        )

        return round(
            score * 100,
            2
        )

    except Exception:
        return 0.0


def check_plagiarism(
    document_text,
    similarity_threshold=70,
    max_sources=5
):
    """
    Search document content against web sources.

    Returns:
        list of dictionaries containing:
        similarity
        url
        title
        snippet
    """

    if not document_text:
        return []

    api_key = get_serpapi_key()

    if not api_key:
        raise ValueError(
            "SERPAPI_KEY is not configured. "
            "Add SERPAPI_KEY to Streamlit Secrets."
        )

    chunks = split_into_chunks(
        document_text,
        chunk_size=80,
        overlap=20
    )

    if not chunks:
        return []

    results = []

    seen_urls = set()

    # Search only a limited number of chunks
    # to avoid excessive SERP API usage.
    chunks_to_search = chunks[:10]

    for chunk in chunks_to_search:

        # Use a meaningful search query.
        query_words = chunk.split()

        if len(query_words) > 35:
            query_words = query_words[:35]

        query = " ".join(
            query_words
        )

        if not query:
            continue

        web_results = search_web(
            query,
            api_key,
            num_results=max_sources
        )

        for item in web_results:

            url = item.get(
                "link",
                ""
            )

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            title = item.get(
                "title",
                ""
            )

            snippet = item.get(
                "snippet",
                ""
            )

            source_text = " ".join(
                [
                    title,
                    snippet
                ]
            )

            similarity = calculate_similarity(
                chunk,
                source_text
            )

            if similarity >= similarity_threshold:

                results.append({
                    "similarity": similarity,
                    "url": url,
                    "title": title,
                    "snippet": snippet
                })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:max_sources]
