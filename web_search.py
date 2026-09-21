import os
import requests
from typing import List, Dict


SERPAPI_URL = "https://serpapi.com/search.json"


def get_serpapi_key():
    """
    Get SerpAPI key from environment variables or Streamlit secrets.
    """

    key = os.getenv("SERPAPI_API_KEY")

    if not key:
        key = os.getenv("SERPAPI_KEY")

    if key:
        return key

    # Streamlit Cloud secrets
    try:
        import streamlit as st

        if "SERPAPI_API_KEY" in st.secrets:
            return st.secrets["SERPAPI_API_KEY"]

        if "SERPAPI_KEY" in st.secrets:
            return st.secrets["SERPAPI_KEY"]

    except Exception:
        pass

    return None


def search_web(
    query: str,
    num_results: int = 5
) -> List[Dict]:
    """
    Search Google through SerpAPI.
    """

    api_key = get_serpapi_key()

    if not api_key:
        raise RuntimeError(
            "SERPAPI_API_KEY is not configured. "
            "Add it to Streamlit Secrets or environment variables."
        )

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": "en",
        "gl": "us"
    }

    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("organic_results", []):

        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        snippet = item.get("snippet", "").strip()

        if not link:
            continue

        results.append({
            "title": title,
            "url": link,
            "snippet": snippet
        })

    return results


def search_multiple(
    queries: List[str],
    results_per_query: int = 5
) -> List[Dict]:
    """
    Search multiple queries and remove duplicate URLs.
    """

    all_results = []

    seen_urls = set()

    for query in queries:

        if not query.strip():
            continue

        try:

            results = search_web(
                query,
                num_results=results_per_query
            )

        except Exception:
            continue

        for result in results:

            url = result.get("url", "")

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            all_results.append(result)

    return all_results


def build_search_queries(
    text: str,
    max_queries: int = 5
) -> List[str]:
    """
    Generate search queries from document content.

    Instead of sending the entire document to Google,
    this extracts meaningful chunks.
    """

    if not text:
        return []

    # Normalize
    text = " ".join(text.split())

    # Split into sentences
    sentences = []

    current = ""

    for word in text.split():

        current += " " + word

        if (
            len(current) >= 180
            and (
                word.endswith(".")
                or word.endswith("?")
                or word.endswith("!")
            )
        ):
            sentences.append(current.strip())
            current = ""

    if current:
        sentences.append(current.strip())

    queries = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 40:
            continue

        # Search distinctive phrase
        query = sentence[:220]

        queries.append(query)

        if len(queries) >= max_queries:
            break

    return queries
