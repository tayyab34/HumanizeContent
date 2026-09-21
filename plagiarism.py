from typing import List, Dict

from embeddings import (
    split_into_chunks,
    create_embeddings,
    create_faiss_index,
    search_faiss
)

from web_search import (
    build_search_queries,
    search_multiple
)


def clean_similarity(score: float) -> float:
    """
    Convert cosine similarity into a percentage.

    Small negative values are treated as zero.
    """

    score = max(0.0, min(1.0, score))

    return round(score * 100, 2)


def check_plagiarism(
    document_text: str,
    similarity_threshold: float = 70,
    max_document_chunks: int = 12,
    max_search_queries: int = 5,
    results_per_query: int = 5,
    top_k: int = 3
) -> List[Dict]:
    """
    Search the web and identify semantically similar passages.

    Returns results in the format expected by app.py:

    {
        "similarity": 82.4,
        "url": "...",
        "snippet": "..."
    }
    """

    if not document_text:
        return []

    # -----------------------------------------
    # 1. Split uploaded document
    # -----------------------------------------

    document_chunks = split_into_chunks(
        document_text,
        chunk_size=700,
        overlap=100
    )

    if not document_chunks:
        return []

    # Limit workload
    document_chunks = document_chunks[
        :max_document_chunks
    ]

    # -----------------------------------------
    # 2. Build search queries
    # -----------------------------------------

    queries = build_search_queries(
        document_text,
        max_queries=max_search_queries
    )

    if not queries:
        return []

    # -----------------------------------------
    # 3. Search Internet
    # -----------------------------------------

    web_results = search_multiple(
        queries,
        results_per_query=results_per_query
    )

    if not web_results:
        return []

    # -----------------------------------------
    # 4. Prepare web snippets
    # -----------------------------------------

    web_texts = []

    for result in web_results:

        text = " ".join([
            result.get("title", ""),
            result.get("snippet", "")
        ]).strip()

        if text:
            web_texts.append(text)

    if not web_texts:
        return []

    # -----------------------------------------
    # 5. Create FAISS RAG index
    # -----------------------------------------

    index, indexed_texts = create_faiss_index(
        web_texts
    )

    # -----------------------------------------
    # 6. Compare document chunks
    # -----------------------------------------

    matches = []

    for chunk in document_chunks:

        retrieved = search_faiss(
            index,
            chunk,
            indexed_texts,
            top_k=top_k
        )

        for match in retrieved:

            similarity = clean_similarity(
                match["score"]
            )

            if similarity < similarity_threshold:
                continue

            matched_text = match["text"]

            # Find original web result
            source = None

            for result in web_results:

                candidate = " ".join([
                    result.get("title", ""),
                    result.get("snippet", "")
                ]).strip()

                if candidate == matched_text:
                    source = result
                    break

            if not source:
                continue

            matches.append({
                "similarity": similarity,
                "url": source.get("url", ""),
                "snippet": source.get(
                    "snippet",
                    matched_text
                ),
                "matched_text": chunk
            })

    # -----------------------------------------
    # 7. Remove duplicate URLs
    # Keep strongest match
    # -----------------------------------------

    best_by_url = {}

    for match in matches:

        url = match["url"]

        if url not in best_by_url:

            best_by_url[url] = match

        elif (
            match["similarity"]
            > best_by_url[url]["similarity"]
        ):

            best_by_url[url] = match

    final_results = list(
        best_by_url.values()
    )

    # -----------------------------------------
    # 8. Sort highest similarity first
    # -----------------------------------------

    final_results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return final_results
