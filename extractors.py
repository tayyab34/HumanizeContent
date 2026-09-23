import io
import re
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".md",
    ".csv",
    ".xlsx",
}


try:
    import fitz
except ImportError:
    fitz = None


try:
    from docx import Document
except ImportError:
    Document = None


try:
    from pptx import Presentation
except ImportError:
    Presentation = None


try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None


def supported_extensions():
    return SUPPORTED_EXTENSIONS


def _read_bytes(file_obj):

    if hasattr(file_obj, "getvalue"):
        return file_obj.getvalue()

    if hasattr(file_obj, "read"):

        file_obj.seek(0)

        return file_obj.read()

    return Path(
        str(file_obj)
    ).read_bytes()


def filename(file_obj):

    return Path(
        getattr(
            file_obj,
            "name",
            str(file_obj),
        )
    ).name


def clean_text(text):

    text = text.replace(
        "\x00",
        " ",
    )

    text = text.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n[ \t]+",
        "\n",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def extract_text_from_file(file_obj):

    ext = Path(
        filename(file_obj)
    ).suffix.lower()

    data = _read_bytes(file_obj)

    if ext not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # PDF
    if ext == ".pdf":

        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is not installed."
            )

        document = fitz.open(
            stream=data,
            filetype="pdf",
        )

        try:

            pages = [
                page.get_text("text")
                for page in document
            ]

        finally:

            document.close()

        text = "\n\n".join(pages)

        return clean_text(text)

    # DOCX
    if ext == ".docx":

        if Document is None:
            raise RuntimeError(
                "python-docx is not installed."
            )

        document = Document(
            io.BytesIO(data)
        )

        parts = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        for table in document.tables:

            for row in table.rows:

                parts.append(
                    " | ".join(
                        cell.text.strip()
                        for cell in row.cells
                    )
                )

        return clean_text(
            "\n".join(parts)
        )

    # PPTX
    if ext == ".pptx":

        if Presentation is None:
            raise RuntimeError(
                "python-pptx is not installed."
            )

        presentation = Presentation(
            io.BytesIO(data)
        )

        parts = []

        for slide in presentation.slides:

            for shape in slide.shapes:

                if (
                    hasattr(shape, "text")
                    and shape.text.strip()
                ):

                    parts.append(
                        shape.text
                    )

        return clean_text(
            "\n".join(parts)
        )

    # XLSX
    if ext == ".xlsx":

        if load_workbook is None:
            raise RuntimeError(
                "openpyxl is not installed."
            )

        workbook = load_workbook(
            io.BytesIO(data),
            read_only=True,
            data_only=True,
        )

        parts = []

        try:

            for worksheet in workbook.worksheets:

                parts.append(
                    f"[Sheet: {worksheet.title}]"
                )

                for row in worksheet.iter_rows(
                    values_only=True
                ):

                    values = [
                        str(value).strip()
                        for value in row
                        if (
                            value is not None
                            and str(value).strip()
                        )
                    ]

                    if values:

                        parts.append(
                            " | ".join(values)
                        )

        finally:

            workbook.close()

        return clean_text(
            "\n".join(parts)
        )

    # TXT / MD / CSV
    return clean_text(
        data.decode(
            "utf-8",
            errors="replace",
        )
    )
