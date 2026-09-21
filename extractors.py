import io

from pypdf import PdfReader
from docx import Document


def extract_text(uploaded_file):
    """
    Extract text from PDF, DOCX, or TXT Streamlit uploaded file.
    """

    filename = uploaded_file.name.lower()

    # -----------------------------
    # TXT
    # -----------------------------
    if filename.endswith(".txt"):

        data = uploaded_file.getvalue()

        return data.decode(
            "utf-8",
            errors="ignore"
        ).strip()

    # -----------------------------
    # PDF
    # -----------------------------
    if filename.endswith(".pdf"):

        data = uploaded_file.getvalue()

        pdf_file = io.BytesIO(data)

        reader = PdfReader(pdf_file)

        pages = []

        for page in reader.pages:

            try:
                text = page.extract_text()

                if text:
                    pages.append(text)

            except Exception:
                continue

        return "\n\n".join(pages).strip()

    # -----------------------------
    # DOCX
    # -----------------------------
    if filename.endswith(".docx"):

        data = uploaded_file.getvalue()

        doc_file = io.BytesIO(data)

        document = Document(doc_file)

        paragraphs = []

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n\n".join(
            paragraphs
        ).strip()

    raise ValueError(
        "Unsupported file type. "
        "Please upload PDF, DOCX, or TXT."
    )
