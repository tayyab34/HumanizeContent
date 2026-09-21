import streamlit as st

st.set_page_config(
    page_title="AI Humanizer + Plagiarism Checker",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Humanizer + Plagiarism Checker")

st.write("Upload a PDF, DOCX, or TXT file.")


# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Document",
    type=["txt", "pdf", "docx"]
)


# --------------------------------------------------
# MAIN TEXT
# --------------------------------------------------

main_text = ""


if uploaded_file is not None:

    try:

        file_name = uploaded_file.name.lower()

        # TXT
        if file_name.endswith(".txt"):

            main_text = uploaded_file.getvalue().decode(
                "utf-8",
                errors="ignore"
            )


        # PDF
        elif file_name.endswith(".pdf"):

            import pymupdf

            pdf_bytes = uploaded_file.getvalue()

            pdf = pymupdf.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            pages = []

            for page in pdf:

                text = page.get_text()

                if text:
                    pages.append(text)

            pdf.close()

            main_text = "\n\n".join(pages)


        # DOCX
        elif file_name.endswith(".docx"):

            from docx import Document
            from io import BytesIO

            document = Document(
                BytesIO(uploaded_file.getvalue())
            )

            paragraphs = []

            for paragraph in document.paragraphs:

                text = paragraph.text.strip()

                if text:
                    paragraphs.append(text)

            main_text = "\n\n".join(paragraphs)


    except Exception as e:

        st.error("Error reading the uploaded file.")

        st.exception(e)

        main_text = ""


# --------------------------------------------------
# DOCUMENT PREVIEW
# --------------------------------------------------

if main_text:

    st.success(
        f"Document loaded successfully: {uploaded_file.name}"
    )

    st.subheader("📖 Document Preview")

    st.text_area(
        "Document Preview",
        value=main_text[:12000],
        height=300
    )


    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    word_count = len(main_text.split())
    character_count = len(main_text)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Words",
            word_count
        )

    with col2:

        st.metric(
            "Characters",
            character_count
        )


    st.divider()


    # --------------------------------------------------
    # ANALYZE
    # --------------------------------------------------

    if st.button(
        "Analyze Document",
        use_container_width=True
    ):

        st.success(
            "Document analyzed successfully."
        )

        st.subheader("Extracted Text")

        st.text_area(
            "Extracted Text",
            value=main_text,
            height=400
        )


else:

    if uploaded_file is not None:

        st.warning(
            "No readable text was found in this document."
        )

    else:

        st.info(
            "Please upload a PDF, DOCX, or TXT file to begin."
        )
