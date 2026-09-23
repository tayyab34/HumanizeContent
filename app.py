import streamlit as st

from extractors import extract_text_from_file, supported_extensions
from plagiarism import analyze_document
from humanizer import humanize_document, gemini_status
from web_search import search_web, format_search_results


st.set_page_config(
    page_title="HumanizeContent - Document Similarity & RAG",
    page_icon="📄",
    layout="wide",
)


st.title("📄 HumanizeContent")

st.caption(
    "Document extraction • reference-corpus similarity • semantic RAG matching • "
    "source discovery • natural rewriting"
)


with st.sidebar:
    st.header("Configuration")

    generation_model = st.text_input(
        "Gemini generation model",
        value="gemini-3.8-flash",
        help="Change this if your Gemini account exposes another generation model.",
    )

    embedding_model = st.text_input(
        "Gemini embedding model",
        value="gemini-embedding-2",
        help="Current Gemini embedding model used for semantic similarity.",
    )

    st.session_state["generation_model"] = generation_model
    st.session_state["embedding_model"] = embedding_model

    status = gemini_status()

    if status["configured"]:
        st.success("Gemini API key detected.")
    else:
        st.warning("Gemini API key not configured.")

    st.markdown("### What this app can verify")

    st.write(
        "It compares your document with reference files you provide and can "
        "retrieve web search results for source discovery."
    )

    st.markdown("### Important")

    st.info(
        "This is not Turnitin. It cannot access Turnitin's proprietary database "
        "or guarantee a Turnitin AI/plagiarism score."
    )

    st.markdown("### Supported")

    st.write(", ".join(sorted(supported_extensions())))


main_file = st.file_uploader(
    "1. Upload the document you want to analyze",
    type=[x.lstrip(".") for x in supported_extensions()],
)


reference_files = st.file_uploader(
    "2. Upload reference/source documents",
    type=[x.lstrip(".") for x in supported_extensions()],
    accept_multiple_files=True,
    help="These files form your local reference corpus.",
)


web_query = st.text_input(
    "Optional web source search",
    placeholder="Enter a topic, sentence, or source to search",
)


if main_file:
    try:
        main_text = extract_text_from_file(main_file)
        st.session_state["main_text"] = main_text

    except Exception as exc:
        st.error(f"Could not extract text: {exc}")
        main_text = ""

else:
    main_text = st.session_state.get("main_text", "")


tab_analysis, tab_rewrite, tab_search, tab_text = st.tabs(
    [
        "🔎 Similarity",
        "✍️ Rewrite",
        "🌐 Source Search",
        "📚 Extracted Text",
    ]
)


# ============================================================
# SIMILARITY
# ============================================================

with tab_analysis:

    st.subheader("Similarity / plagiarism signals")

    if st.button(
        "Analyze document",
        type="primary",
        use_container_width=True,
    ):

        if not main_file:
            st.error("Upload the main document first.")

        elif not main_text.strip():
            st.error("The document contains no readable text.")

        else:

            with st.spinner(
                "Building comparison index and analyzing passages..."
            ):

                try:

                    report = analyze_document(
                        main_text=main_text,
                        reference_files=reference_files,
                        use_gemini_embeddings=True,
                        embedding_model=st.session_state[
                            "embedding_model"
                        ],
                    )

                    st.session_state["report"] = report

                except Exception as exc:
                    st.exception(exc)

    report = st.session_state.get("report")

    if report:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Words",
            f"{report['word_count']:,}",
        )

        c2.metric(
            "Sentences",
            f"{report['sentence_count']:,}",
        )

        c3.metric(
            "Reference files",
            f"{report['reference_count']:,}",
        )

        c4.metric(
            "Reference chunks",
            f"{report['reference_chunk_count']:,}",
        )

        st.markdown("### Overall local similarity")

        if report["overall_similarity"] is None:

            st.info(
                "No reference documents were supplied. A "
                "plagiarism/similarity percentage cannot be calculated "
                "without a comparison corpus."
            )

        else:

            st.metric(
                "Highest-source similarity",
                f"{report['overall_similarity']:.1f}%",
            )

        st.markdown("### Source-by-source similarity")

        if report["source_scores"]:

            for row in report["source_scores"]:

                st.write(
                    f"**{row['source']}** — "
                    f"{row['similarity']:.1f}% "
                    f"({row['method']})"
                )

        else:

            st.info(
                "No readable reference source was supplied."
            )

        st.markdown("### Potential overlapping passages")

        if report["matches"]:

            for i, match in enumerate(
                report["matches"],
                1,
            ):

                title = (
                    f"Match {i} · {match['source']} · "
                    f"semantic "
                    f"{match['semantic_similarity']:.1f}% · "
                    f"phrase "
                    f"{match['phrase_overlap']:.1f}%"
                )

                with st.expander(title):

                    st.markdown(
                        "**Your document:**"
                    )

                    st.write(
                        match["query_excerpt"]
                    )

                    st.markdown(
                        "**Reference source:**"
                    )

                    st.write(
                        match["reference_excerpt"]
                    )

                    st.caption(
                        "This is a similarity signal requiring human review. "
                        "Similarity alone does not establish plagiarism."
                    )

        else:

            st.success(
                "No significant overlap was detected against the supplied "
                "reference corpus."
            )

        st.markdown("### AI detector")

        st.info(
            "No Turnitin AI score is shown. Turnitin's proprietary AI detector "
            "is not available through this application."
        )


# ============================================================
# REWRITE
# ============================================================

with tab_rewrite:

    st.subheader(
        "Rewrite for natural, clear expression"
    )

    st.write(
        "The rewrite keeps the original meaning and asks the model not to "
        "invent facts, citations, quotations, or statistics."
    )

    rewrite_text = st.text_area(
        "Text",
        value=st.session_state.get(
            "humanized_text",
            main_text,
        ),
        height=350,
    )

    style = st.selectbox(
        "Style",
        [
            "Academic and formal",
            "Natural professional",
            "Clear and concise",
            "Plain English",
        ],
    )

    preserve = st.checkbox(
        "Preserve citations, references, names, dates, numbers and technical terms",
        value=True,
    )

    if st.button(
        "Rewrite",
        type="primary",
        use_container_width=True,
    ):

        if not rewrite_text.strip():

            st.error(
                "Enter or upload text first."
            )

        else:

            with st.spinner(
                "Rewriting document sections..."
            ):

                try:

                    result = humanize_document(
                        text=rewrite_text,
                        style=style,
                        preserve_citations=preserve,
                        model=st.session_state[
                            "generation_model"
                        ],
                    )

                    st.session_state[
                        "humanized_text"
                    ] = result["text"]

                    st.session_state[
                        "rewrite_notes"
                    ] = result["notes"]

                except Exception as exc:
                    st.exception(exc)

    if st.session_state.get(
        "humanized_text"
    ):

        st.markdown(
            "### Rewritten text"
        )

        st.text_area(
            "Result",
            value=st.session_state[
                "humanized_text"
            ],
            height=550,
        )

        st.download_button(
            "Download rewritten TXT",
            data=st.session_state[
                "humanized_text"
            ],
            file_name="rewritten_document.txt",
            mime="text/plain",
            use_container_width=True,
        )

        if st.session_state.get(
            "rewrite_notes"
        ):

            st.markdown(
                "### Processing notes"
            )

            st.write(
                st.session_state[
                    "rewrite_notes"
                ]
            )


# ============================================================
# WEB SEARCH
# ============================================================

with tab_search:

    st.subheader(
        "Web source discovery"
    )

    st.caption(
        "Search is for finding sources to review. It is not a substitute "
        "for Turnitin's proprietary corpus."
    )

    if st.button(
        "Search web",
        use_container_width=True,
    ):

        if not web_query.strip():

            st.error(
                "Enter a search query."
            )

        else:

            with st.spinner(
                "Searching..."
            ):

                try:

                    results = search_web(
                        web_query,
                        max_results=8,
                    )

                    st.session_state[
                        "web_results"
                    ] = results

                except Exception as exc:
                    st.exception(exc)

    results = st.session_state.get(
        "web_results",
        [],
    )

    if results:

        st.markdown(
            format_search_results(
                results
            )
        )


# ============================================================
# EXTRACTED TEXT
# ============================================================

with tab_text:

    if main_text:

        st.text_area(
            "Extracted text",
            value=main_text,
            height=650,
        )

    else:

        st.info(
            "Upload a document to see extracted text."
        )
