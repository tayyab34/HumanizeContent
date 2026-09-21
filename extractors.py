import pymupdf
import docx


def extract_pdf(file):
    text = ""

    pdf = pymupdf.open(stream=file.read(), filetype="pdf")

    for page in pdf:
        text += page.get_text()

    return text


def extract_docx(file):
    doc = docx.Document(file)

    return "\n".join(
        para.text
        for para in doc.paragraphs
    )


def extract_txt(file):
    return file.read().decode("utf-8")


def extract_text(uploaded_file):

    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return extract_pdf(uploaded_file)

    if name.endswith(".docx"):
        return extract_docx(uploaded_file)

    if name.endswith(".txt"):
        return extract_txt(uploaded_file)

    return ""
