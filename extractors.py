import io
import re

from pypdf import PdfReader
from docx import Document


def clean_text(text):

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def extract_text(uploaded_file):

    if uploaded_file is None:
        return ""


    filename = uploaded_file.name.lower()


    # TXT
    if filename.endswith(".txt"):

        raw = uploaded_file.getvalue()

        text = raw.decode(
            "utf-8",
            errors="ignore"
        )

        return clean_text(text)


    # PDF
    if filename.endswith(".pdf"):

        raw = uploaded_file.getvalue()

        pdf = PdfReader(
            io.BytesIO(raw)
        )

        pages = []

        for page in pdf.pages:

            try:

                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            except Exception:
                continue

        return clean_text(
            "\n\n".join(pages)
        )


    # DOCX
    if filename.endswith(".docx"):

        raw = uploaded_file.getvalue()

        document = Document(
            io.BytesIO(raw)
        )

        paragraphs = []


        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)


        # Tables
        for table in document.tables:

            for row in table.rows:

                cells = []

                for cell in row.cells:

                    value = cell.text.strip()

                    if value:
                        cells.append(value)


                if cells:

                    paragraphs.append(
                        " ".join(cells)
                    )


        return clean_text(
            "\n\n".join(paragraphs)
        )


    raise ValueError(
        "Unsupported file type. "
        "Please upload PDF, DOCX, or TXT."
    )
