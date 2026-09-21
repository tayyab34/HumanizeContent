import streamlit as st
from io import BytesIO

# PDF
try:
    import pymupdf
except Exception:
    pymupdf = None

# DOCX
try:
    from docx import Document
except Exception:
    Document = None


def extract_text(uploaded_file):
    """
    Extract text from TXT, PDF, DOCX
    """
    file_name = uploaded_file.name.lower()

    try:
        # TXT
        if file_name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")

        # PDF
        elif file_name.endswith(".pdf"):
            if pymupdf is None:
                return "PyMuPDF is not installed."

            text = ""
            pdf_bytes = uploaded_file.read()

            pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")

            for page in pdf:
                text += page.get_text()

            pdf.close()

            return text

        # DOCX
        elif file_name.endswith(".docx"):
            if Document is None:
                return "python-docx is not installed."

            doc = Document(BytesIO(uploaded_file.read()))

            return "\n".join(
                para.text for para in doc.paragraphs
            )

        return "Unsupported file type."

    except Exception as ex:
        return f"Error reading file: {str(ex)}"


# -------------------------
# STREAMLIT APP
# -------------------------

st.set_page_config(
    page_title="AI Humanizer + Plagiarism Checker",
    layout="wide"
)

st.title("AI Humanizer + Plagiarism Checker")

uploaded_file = st.file_uploader(
    "Upload Document",
    type=["txt", "pdf", "docx"]
)

document_text = ""

if uploaded_file is not None:

    document_text = extract_text(uploaded_file)

    st.subheader("Document Preview")

    st.text_area(
        label="Document Preview",
        value=document_text[:12000] if document_text else "",
        height=300
    )

    st.info(
        f"Characters: {len(document_text)}"
    )

    if st.button("Analyze"):

        st.success("Document processed successfully")

        word_count = len(document_text.split())

        st.write(f"Word Count: {word_count}")
        st.write(f"Character Count: {len(document_text)}")

        st.subheader("Humanized Preview")

        humanized_text = document_text

        st.text_area(
            label="Humanized Text",
            value=humanized_text[:5000],
            height=250
        )
