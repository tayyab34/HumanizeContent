import re

import numpy as np

from embeddings import (
    available as embeddings_available,
)

from embeddings import (
    cosine_similarity,
    embed_texts,
)

from extractors import (
    extract_text_from_file,
    filename,
)


try:

    from sklearn.feature_extraction.text import (
        TfidfVectorizer,
    )

    from sklearn.metrics.pairwise import (
        cosine_similarity as sklearn_cosine,
    )

except ImportError:

    TfidfVectorizer = None
    sklearn_cosine = None


def normalize(text):

    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def words(text):

    return re.findall(
        r"\b[\w'-]+\b",
        text,
    )


def word_count(text):

    return len(
        words(text)
    )


def sentence_count(text):

    if not text.strip():
        return 0

    return len(
        [
            x
            for x in re.split(
                r"(?<=[.!?])\s+",
                normalize(text),
            )
            if x.strip()
        ]
    )


def chunks(
    text,
    max_words=160,
    overlap=30,
):

    word_list = text.split()

    if not word_list:
        return []

    output = []

    start = 0

    while start < len(word_list):

        end = min(
            len(word_list),
            start + max_words,
        )

        output.append(
            " ".join(
                word_list[start:end]
            )
        )

        if end == len(word_list):
            break

        start = max(
            start + 1,
            end - overlap,
        )

    return output


def shingles(
    text,
    size=8,
):

    word_list = re.findall(
        r"\b[\w'-]+\b",
        normalize(text),
    )

    if len(word_list) < size:
        return set()

    return {
        " ".join(
            word_list[i:i + size]
        )
        for i in range(
            len(word_list) - size + 1
        )
    }


def phrase_overlap(
    query,
    reference,
):

    query_shingles = shingles(
        query
    )

    reference_shingles = shingles(
        reference
    )

    if not query_shingles:
        return 0.0

    return (
        len(
            query_shingles
            & reference_shingles
        )
        / len(query_shingles)
        * 100.0
    )


def tfidf_similarity(
    query_chunks,
    reference_chunks,
):

    if (
        not query_chunks
        or not reference_chunks
        or TfidfVectorizer is None
        or sklearn_cosine is None
    ):

        return None

    try:

        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=40000,
        )

        matrix = vectorizer.fit_transform(
            query_chunks
            + reference_chunks
        )

        q_matrix = matrix[
            :len(query_chunks)
        ]

        r_matrix = matrix[
            len(query_chunks):
        ]

        scores = sklearn_cosine(
            q_matrix,
            r_matrix,
        )

        return scores

    except ValueError:

        return None


def compare_chunks(
    query_chunks,
    reference_chunks,
    embedding_model="gemini-embedding-2",
):

    """
    Returns one best reference match for every query chunk.

    Gemini embeddings are used when available.
    TF-IDF is used as a local fallback.
    """

    semantic_matrix = None

    method = "TF-IDF"

    if embeddings_available():

        try:

            all_texts = (
                query_chunks
                + reference_chunks
            )

            vectors = embed_texts(
                all_texts,
                model=embedding_model,
                output_dimensionality=768,
            )

            query_vectors = vectors[
                :len(query_chunks)
            ]

            reference_vectors = vectors[
                len(query_chunks):
            ]

            semantic_matrix = np.array(
                [
                    [
                        cosine_similarity(
                            q,
                            r,
                        )
                        for r in reference_vectors
                    ]
                    for q in query_vectors
                ]
            )

            method = (
                "Gemini semantic embeddings"
            )

        except Exception:

            semantic_matrix = None

    if semantic_matrix is None:

        tfidf = tfidf_similarity(
            query_chunks,
            reference_chunks,
        )

        if tfidf is None:

            return [], "keyword fallback"

        semantic_matrix = tfidf

        method = "TF-IDF"

    matches = []

    for query_index, query_chunk in enumerate(
        query_chunks
    ):

        row = semantic_matrix[
            query_index
        ]

        if len(row) == 0:
            continue

        reference_index = int(
            np.argmax(row)
        )

        score = float(
            row[reference_index]
            * 100.0
        )

        reference_chunk = (
            reference_chunks[
                reference_index
            ]
        )

        phrase_score = phrase_overlap(
            query_chunk,
            reference_chunk,
        )

        matches.append(
            {
                "query": query_chunk,
                "reference": reference_chunk,
                "semantic_similarity": score,
                "phrase_overlap": phrase_score,
                "reference_index": reference_index,
            }
        )

    return matches, method


def analyze_document(
    main_text,
    reference_files,
    use_gemini_embeddings=True,
    embedding_model="gemini-embedding-2",
    max_matches=40,
):

    reference_documents = []

    for file_obj in (
        reference_files or []
    ):

        try:

            text = extract_text_from_file(
                file_obj
            )

            if text.strip():

                reference_documents.append(
                    {
                        "source": filename(
                            file_obj
                        ),
                        "text": text,
                    }
                )

        except Exception as exc:

            reference_documents.append(
                {
                    "source": filename(
                        file_obj
                    ),
                    "text": "",
                    "error": str(exc),
                }
            )

    query_chunks = chunks(
        main_text
    )

    all_matches = []

    source_scores = []

    total_reference_chunks = 0

    for reference in reference_documents:

        if not reference["text"]:
            continue

        reference_chunks = chunks(
            reference["text"]
        )

        total_reference_chunks += len(
            reference_chunks
        )

        if (
            not query_chunks
            or not reference_chunks
        ):
            continue

        matches, method = compare_chunks(
            query_chunks,
            reference_chunks,
            embedding_model=embedding_model,
        )

        if matches:

            scores = sorted(
                [
                    m["semantic_similarity"]
                    for m in matches
                ],
                reverse=True,
            )

            top_n = max(
                1,
                int(
                    len(scores)
                    * 0.25
                ),
            )

            source_similarity = float(
                np.mean(
                    scores[:top_n]
                )
            )

            source_scores.append(
                {
                    "source": reference[
                        "source"
                    ],
                    "similarity": source_similarity,
                    "method": method,
                }
            )

            for match in matches:

                if (
                    match[
                        "semantic_similarity"
                    ] >= 50.0
                    or
                    match[
                        "phrase_overlap"
                    ] >= 2.0
                ):

                    all_matches.append(
                        {
                            "source": reference[
                                "source"
                            ],
                            "semantic_similarity":
                                match[
                                    "semantic_similarity"
                                ],
                            "phrase_overlap":
                                match[
                                    "phrase_overlap"
                                ],
                            "query_excerpt":
                                match[
                                    "query"
                                ][:1400],
                            "reference_excerpt":
                                match[
                                    "reference"
                                ][:1400],
                        }
                    )

    source_scores.sort(
        key=lambda item: item[
            "similarity"
        ],
        reverse=True,
    )

    all_matches.sort(
        key=lambda item: (
            item["phrase_overlap"],
            item["semantic_similarity"],
        ),
        reverse=True,
    )

    unique = []

    seen = set()

    for match in all_matches:

        key = (
            match["source"],
            normalize(
                match["query_excerpt"]
            )[:250],
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            match
        )

    return {

        "word_count":
            word_count(
                main_text
            ),

        "sentence_count":
            sentence_count(
                main_text
            ),

        "reference_count":
            len(
                reference_documents
            ),

        "reference_chunk_count":
            total_reference_chunks,

        "overall_similarity": (
            source_scores[0][
                "similarity"
            ]
            if source_scores
            else None
        ),

        "source_scores":
            source_scores,

        "matches":
            unique[:max_matches],
    }
