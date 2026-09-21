import pymupdf
import docx


def extract_pdf(file):
    text_parts = []

    pdf = pymupdf.open(
        stream=file.read(),
        filetype="pdf"
    )

    try:
        for page in pdf:
            page_text = page.get_text()

            if page_text:
                text_parts.append(page_text)

    finally:
        pdf.close()

    return "\n".join(text_parts).strip()


def extract_docx(file):
    doc = docx.Document(file)

    text_parts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()

        if text:
            text_parts.append(text)

    return "\n".join(text_parts).strip()


def extract_txt(file):

    data = file.read()

    try:
        return data.decode("utf-8").strip()

    except UnicodeDecodeError:
        return data.decode(
            "utf-8",
            errors="ignore"
        ).strip()


def extract_text(uploaded_file):

    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return extract_pdf(uploaded_file)

    if name.endswith(".docx"):
        return extract_docx(uploaded_file)

    if name.endswith(".txt"):
        return extract_txt(uploaded_file)

    raise ValueError(
        "Unsupported file type. Please upload PDF, DOCX, or TXT."
    )
