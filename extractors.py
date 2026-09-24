import io
import os

from pypdf import PdfReader
from docx import Document


SUPPORTED_EXTENSIONS = [
    "txt",
    "pdf",
    "docx"
]


def supported_extensions():
    return SUPPORTED_EXTENSIONS


def extract_text_from_file(uploaded_file):

    filename = uploaded_file.name.lower()

    data = uploaded_file.getvalue()

    # -----------------------------------------
    # TXT
    # -----------------------------------------

    if filename.endswith(".txt"):

        return data.decode(
            "utf-8",
            errors="ignore"
        )

    # -----------------------------------------
    # PDF
    # -----------------------------------------

    if filename.endswith(".pdf"):

        reader = PdfReader(
            io.BytesIO(data)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n".join(pages)

    # -----------------------------------------
    # DOCX
    # -----------------------------------------

    if filename.endswith(".docx"):

        document = Document(
            io.BytesIO(data)
        )

        paragraphs = []

        for paragraph in document.paragraphs:

            if paragraph.text.strip():

                paragraphs.append(
                    paragraph.text
                )

        return "\n".join(paragraphs)

    raise ValueError(
        f"Unsupported file type: {filename}"
    )
