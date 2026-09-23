import os
import re
import requests
import streamlit as st

from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_serpapi_key():
    try:
        key = st.secrets.get("SERPAPI_KEY", "")
    except Exception:
        key = ""

    if not key:
        key = os.getenv("SERPAPI_KEY", "")

    return key


def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_into_chunks(text, chunk_size=120, overlap=30):

    text = clean_text(text)

    if not text:
        return []

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = min(start + chunk_size, len(words))

        chunk = " ".join(words[start:end])

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def search_web(query, api_key, num_results=5):

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

        return data.get("organic_results", [])

    except Exception:
        return []


def extract_page_text(url):

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav"
            ]
        ):
            tag.decompose()

        text = soup.get_text(" ")

        text = clean_text(text)

        return text[:50000]

    except Exception:
        return ""


def calculate_similarity(text1, text2):

    if not text1 or not text2:
        return 0.0

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        vectors = vectorizer.fit_transform(
            [text1, text2]
        )

        score = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

        return round(score * 100, 2)

    except Exception:
        return 0.0


def check_plagiarism(
    document_text,
    similarity_threshold=20,
    max_sources=10
):

    if not document_text:
        return []

    api_key = get_serpapi_key()

    if not api_key:
        raise ValueError(
            "SERPAPI_KEY not found."
        )

    chunks = split_into_chunks(
        document_text,
        chunk_size=120,
        overlap=30
    )

    if not chunks:
        return []

    results = []

    seen_urls = set()

    chunks_to_search = chunks[:10]

    for chunk in chunks_to_search:

        words = chunk.split()

        query_text = " ".join(words[:20])

        if not query_text:
            continue

        query = f'"{query_text}"'

        search_results = search_web(
            query,
            api_key,
            num_results=5
        )

        for item in search_results:

            url = item.get("link", "")

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

            page_text = extract_page_text(
                url
            )

            if not page_text:
                continue

            similarity = calculate_similarity(
                chunk,
                page_text
            )

            if similarity >= similarity_threshold:

                results.append(
                    {
                        "similarity": similarity,
                        "url": url,
                        "title": title,
                        "snippet": snippet
                    }
                )

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:max_sources]
