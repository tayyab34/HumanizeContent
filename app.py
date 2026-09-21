import streamlit as st
from extractors import extract_text
from embeddings import create_faiss_index
from plagiarism import check_plagiarism
from humanizer import humanize_text

st.set_page_config(
    page_title="Humanize RAG",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Content Humanizer + Plagiarism Checker")

with st.sidebar:
    st.header("Settings")

    similarity_threshold = st.slider(
        "Similarity Threshold %",
        0,
        100,
        70
    )

uploaded_file = st.file_uploader(
    "Upload PDF / DOCX / TXT",
    type=["pdf", "docx", "txt"]
)

if uploaded_file:

    with st.spinner("Extracting text..."):
        document_text = extract_text(uploaded_file)

    st.success("Document loaded")

    st.subheader("Document Preview")

    st.text_area(
        "Text",
        document_text[:5000],
        height=250
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button("Check Plagiarism"):

            with st.spinner("Searching web..."):

                results = check_plagiarism(
                    document_text,
                    similarity_threshold
                )

            st.subheader("Plagiarism Results")

            if not results:
                st.success("No significant matches found.")

            else:

                for item in results:

                    st.markdown("---")

                    st.write(
                        f"Similarity: {item['similarity']}%"
                    )

                    st.write(
                        f"Source: {item['url']}"
                    )

                    st.write(
                        item["snippet"]
                    )

    with col2:

        if st.button("Humanize Content"):

            with st.spinner("Humanizing content..."):

                humanized = humanize_text(
                    document_text
                )

            st.subheader("Humanized Output")

            st.text_area(
                "Result",
                humanized,
                height=400
            )

            st.download_button(
                "Download",
                humanized,
                file_name="humanized.txt"
            )
