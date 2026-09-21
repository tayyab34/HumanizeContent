import streamlit as st

st.set_page_config(
    page_title="Humanize RAG",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Content Humanizer + Plagiarism Checker")

# Import after Streamlit starts so import errors are easier to identify
try:
    from extractors import extract_text
except Exception as e:
    st.error("Could not load extractors.py")
    st.exception(e)
    st.stop()

try:
    from plagiarism import check_plagiarism
except Exception as e:
    st.error("Could not load plagiarism.py")
    st.exception(e)
    st.stop()

try:
    from humanizer import humanize_text
except Exception as e:
    st.error("Could not load humanizer.py")
    st.exception(e)
    st.stop()


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
        "Higher values show stronger semantic matches."
    )


uploaded_file = st.file_uploader(
    "Upload PDF / DOCX / TXT",
    type=["pdf", "docx", "txt"]
)


if uploaded_file is not None:

    # -------------------------
    # EXTRACT TEXT
    # -------------------------

    with st.spinner("Reading document..."):

        try:
            main_text = extract_text(uploaded_file)

        except Exception as e:
            st.error("Could not extract text from this file.")
            st.exception(e)
            st.stop()


    if not main_text or not main_text.strip():

        st.warning(
            "No readable text was found in the uploaded document."
        )

        st.stop()


    st.success(
        f"Document loaded: {uploaded_file.name}"
    )


    # -------------------------
    # DOCUMENT INFORMATION
    # -------------------------

    st.subheader("📖 Document Preview")

    st.text_area(
        "Extracted document text",
        value=main_text[:12000],
        height=300
    )


    word_count = len(main_text.split())
    character_count = len(main_text)


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
            "Threshold",
            f"{similarity_threshold}%"
        )


    st.divider()


    # -------------------------
    # TWO COLUMNS
    # -------------------------

    left, right = st.columns(2)


    # =====================================================
    # PLAGIARISM
    # =====================================================

    with left:

        st.subheader("🔎 Web Similarity Check")

        check_button = st.button(
            "Check Plagiarism",
            use_container_width=True
        )


        if check_button:

            with st.spinner(
                "Searching web sources and comparing content..."
            ):

                try:

                    results = check_plagiarism(
                        document_text=main_text,
                        similarity_threshold=similarity_threshold
                    )

                except Exception as e:

                    st.error(
                        "Plagiarism check failed."
                    )

                    st.exception(e)

                    results = []


            if not results:

                st.success(
                    "No significant web-source matches were found."
                )

            else:

                st.warning(
                    f"{len(results)} potential match(es) found."
                )


                for number, item in enumerate(
                    results,
                    start=1
                ):

                    st.markdown(
                        f"### Match {number}"
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


    # =====================================================
    # HUMANIZER
    # =====================================================

    with right:

        st.subheader("✍️ Humanize Content")


        humanize_button = st.button(
            "Humanize Content",
            use_container_width=True
        )


        if humanize_button:

            with st.spinner(
                "Rewriting content..."
            ):

                try:

                    humanized = humanize_text(
                        main_text
                    )

                except Exception as e:

                    st.error(
                        "Humanization failed."
                    )

                    st.exception(e)

                    humanized = ""


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
