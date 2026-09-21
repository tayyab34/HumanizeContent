import re
from typing import List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def get_embedding_model():
    """
    Load the embedding model once and reuse it.
    """
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def split_into_chunks(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100
) -> List[str]:
    """
    Split text into reasonably sized chunks.

    The chunks are sentence-aware where possible.
    """

    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    chunks = []
    current = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if len(current) + len(sentence) <= chunk_size:

            if current:
                current += " " + sentence
            else:
                current = sentence

        else:

            if current:
                chunks.append(current)

            # Character overlap
            if overlap > 0 and current:
                overlap_text = current[-overlap:]
            else:
                overlap_text = ""

            current = (
                overlap_text + " " + sentence
            ).strip()

    if current:
        chunks.append(current)

    return chunks


def create_embeddings(
    texts: List[str]
) -> np.ndarray:
    """
    Convert text chunks into normalized embeddings.
    """

    if not texts:
        return np.empty((0, 384), dtype="float32")

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return embeddings.astype("float32")


def create_faiss_index(
    texts: List[str]
) -> Tuple[faiss.Index, List[str]]:
    """
    Create a FAISS cosine-similarity index.

    Because embeddings are normalized, inner product
    is equivalent to cosine similarity.
    """

    if not texts:
        raise ValueError(
            "Cannot create FAISS index from empty text."
        )

    embeddings = create_embeddings(texts)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index, texts


def search_faiss(
    index: faiss.Index,
    query: str,
    texts: List[str],
    top_k: int = 5
):
    """
    Search the FAISS index for semantically similar text.
    """

    if index is None or index.ntotal == 0:
        return []

    query_embedding = create_embeddings([query])

    scores, indices = index.search(
        query_embedding,
        min(top_k, index.ntotal)
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0:
            continue

        results.append({
            "text": texts[idx],
            "score": float(score)
        })

    return results
