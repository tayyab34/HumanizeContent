```python
import streamlit as st

from extractors import extract_text
from plagiarism import check_plagiarism
from humanizer import humanize_text


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Humanize RAG",
    page_icon="📄",
    layout="wide"
)


# ==========================================
# HEADER
# ==========================================

st.title("📄 AI Content Humanizer + Plagiarism Checker")

st.write(
    "Upload a PDF, DOCX, or TXT document to check "
    "web-source similarity and rewrite the content."
)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.header("⚙️ Settings")

    similarity_threshold = st.slider(
        "Similarity Threshold %",
        min_value=0,
        max_value=100,
        value=70,
        step=5
    )

    st.caption(
        "Higher values show only stronger semantic matches."
    )


# ==========================================
# FILE UPLOAD
# ==========================================

uploaded_file = st.file_uploader(
    "Upload PDF / DOCX / TXT",
    type=["pdf", "docx", "txt"]
)


# ==========================================
# PROCESS FILE
# ==========================================

if uploaded_file:

    # --------------------------------------
    # Extract text
    # --------------------------------------

    with st.spinner("Extracting document text..."):

        try:

            main_text = extract_text(
                uploaded_file
            )

        except Exception as e:

            st.error(
                f"Could not read the file: {e}"
            )

            st.stop()


    # --------------------------------------
    # Empty document check
    # --------------------------------------

    if not main_text:

        st.warning(
            "No readable text was found in this document."
        )

        st.stop()


    st.success(
        f"Document loaded successfully: {uploaded_file.name}"
    )


    # ======================================
    # DOCUMENT PREVIEW
    # ======================================

    st.subheader("📖 Document Preview")

    st.text_area(
        "Extracted document text",
        value=main_text[:12000],
        height=300
    )


    # ======================================
    # STATISTICS
    # ======================================

    word_count = len(
        main_text.split()
    )

    character_count = len(
        main_text
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Words",
            f"{word_count:,}"
        )

    with col2:
        st.metric(
            "Characters",
            f"{character_count:,}"
        )

    with col3:
        st.metric(
            "Similarity Threshold",
            f"{similarity_threshold}%"
        )


    st.divider()


    # ======================================
    # TWO MAIN ACTIONS
    # ======================================

    col1, col2 = st.columns(2)


    # ======================================
    # PLAGIARISM CHECK
    # ======================================

    with col1:

        st.subheader("🔎 Plagiarism / Similarity")

        if st.button(
            "Check Plagiarism",
            use_container_width=True
        ):

            with st.spinner(
                "Searching web sources and comparing content..."
            ):

                try:

                    results = check_plagiarism(
                        main_text,
                        similarity_threshold
                    )

                except Exception as e:

                    st.error(
                        f"Plagiarism check failed: {e}"
                    )

                    results = None


            if results is None:

                st.stop()


            if not results:

                st.success(
                    "No significant web-source matches were found."
                )

            else:

                st.warning(
                    f"{len(results)} potential web-source "
                    "match(es) found."
                )


                for index, item in enumerate(
                    results,
                    start=1
                ):

                    st.markdown(
                        f"### Match {index}"
                    )

                    similarity = item.get(
                        "similarity",
                        0
                    )

                    st.metric(
                        "Semantic Similarity",
                        f"{similarity}%"
                    )

                    url = item.get(
                        "url",
                        ""
                    )

                    if url:

                        st.markdown(
                            f"**Source:** [{url}]({url})"
                        )


                    snippet = item.get(
                        "snippet",
                        ""
                    )

                    if snippet:

                        st.write(
                            "**Web Source:**"
                        )

                        st.info(
                            snippet
                        )


                    matched_text = item.get(
                        "matched_text",
                        ""
                    )

                    if matched_text:

                        st.write(
                            "**Matching Document Text:**"
                        )

                        st.warning(
                            matched_text
                        )

                    st.divider()


    # ======================================
    # HUMANIZER
    # ======================================

    with col2:

        st.subheader("✍️ Humanize Content")

        if st.button(
            "Humanize Content",
            use_container_width=True
        ):

            with st.spinner(
                "Rewriting content..."
            ):

                try:

                    humanized = humanize_text(
                        main_text
                    )

                except Exception as e:

                    st.error(
                        f"Humanization failed: {e}"
                    )

                    humanized = None


            if humanized:

                st.success(
                    "Content rewritten successfully."
                )


                st.text_area(
                    "Humanized Output",
                    value=humanized,
                    height=400
                )


                st.download_button(
                    "⬇️ Download Humanized TXT",
                    data=humanized,
                    file_name="humanized.txt",
                    mime="text/plain",
                    use_container_width=True
                )
```
