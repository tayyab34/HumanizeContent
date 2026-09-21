import streamlit as st

from extractors import extract_text
from plagiarism import check_plagiarism
from humanizer import humanize_text


st.set_page_config(
    page_title="Humanize RAG",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Content Humanizer + Plagiarism Checker")
st.caption("RAG-based document analysis with web-source similarity checking")


with st.sidebar:
    st.header("Settings")

    similarity_threshold = st.slider(
        "Similarity Threshold (%)",
        min_value=0,
        max_value=100,
        value=70,
        step=5
    )

    max_sources = st.number_input(
        "Maximum web sources",
        min_value=1,
        max_value=10,
        value=5,
        step=1
    )


uploaded_file = st.file_uploader(
    "Upload PDF / DOCX / TXT",
    type=["pdf", "docx", "txt"]
)


if uploaded_file is None:
    st.info("Upload a document to begin.")
    st.stop()


try:
    with st.spinner("Extracting text..."):
        document_text = extract_text(uploaded_file)

except Exception as e:
    st.error(f"Could not read the document: {e}")
    st.stop()


if not document_text or not document_text.strip():
    st.error("No readable text was found in this document.")
    st.stop()


st.success(
    f"Document loaded successfully — {len(document_text):,} characters"
)


st.subheader("Document Preview")

st.text_area(
    "Extracted Text",
    document_text[:10000],
    height=300
)


col1, col2 = st.columns(2)


with col1:

    st.subheader("🔎 Plagiarism Checker")

    if st.button(
        "Check Plagiarism",
        type="primary",
        use_container_width=True
    ):

        with st.spinner("Searching web sources and calculating similarity..."):

            try:
                results = check_plagiarism(
                    document_text,
                    similarity_threshold,
                    max_sources
                )

            except Exception as e:
                st.error(f"Plagiarism check failed: {e}")
                results = []


        if not results:
            st.success(
                "No significant matching web sources were found."
            )

        else:

            st.warning(
                f"{len(results)} potentially similar source(s) found."
            )

            for index, item in enumerate(results, start=1):

                st.markdown("---")

                st.markdown(
                    f"### Source {index}"
                )

                similarity = item.get(
                    "similarity",
                    0
                )

                st.metric(
                    "Similarity",
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
                    st.write(snippet)


with col2:

    st.subheader("✍️ Humanize Content")

    if st.button(
        "Humanize Content",
        type="primary",
        use_container_width=True
    ):

        with st.spinner("Humanizing content..."):

            try:
                humanized = humanize_text(
                    document_text
                )

            except Exception as e:
                st.error(f"Humanization failed: {e}")
                humanized = ""


        if humanized:

            st.success("Content processed successfully.")

            st.text_area(
                "Humanized Output",
                humanized,
                height=500
            )

            st.download_button(
                "⬇️ Download Humanized TXT",
                data=humanized,
                file_name="humanized.txt",
                mime="text/plain",
                use_container_width=True
            )
