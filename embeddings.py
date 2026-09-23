import os
from typing import List


try:
    from google import genai
    from google.genai import types

except ImportError:

    genai = None
    types = None


def _api_key():

    try:

        import streamlit as st

        value = st.secrets.get(
            "GEMINI_API_KEY",
            "",
        )

        if value:
            return value

    except Exception:
        pass

    return os.getenv(
        "GEMINI_API_KEY",
        "",
    )


def available():

    return bool(
        _api_key()
        and genai is not None
    )


def _client():

    if genai is None:

        raise RuntimeError(
            "google-genai is not installed. "
            "Add google-genai to requirements.txt."
        )

    key = _api_key()

    if not key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=key
    )


def embed_texts(
    texts: List[str],
    model: str = "gemini-embedding-2",
    output_dimensionality: int = 768,
) -> List[List[float]]:

    """
    Generate semantic embeddings with Gemini.
    """

    if not texts:
        return []

    client = _client()

    result = client.models.embed_content(
        model=model,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=output_dimensionality,
        ),
    )

    embeddings = []

    for item in result.embeddings:

        embeddings.append(
            list(item.values)
        )

    return embeddings


def cosine_similarity(a, b):

    if not a or not b:
        return 0.0

    numerator = sum(
        x * y
        for x, y in zip(a, b)
    )

    denominator_a = sum(
        x * x
        for x in a
    ) ** 0.5

    denominator_b = sum(
        y * y
        for y in b
    ) ** 0.5

    denominator = (
        denominator_a
        * denominator_b
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator
