import os
import re

from difflib import SequenceMatcher


try:

    from google import genai

except ImportError:

    genai = None


def api_key():

    try:

        import streamlit as st

        value = st.secrets.get(
            "GEMINI_API_KEY",
            "",
        )

        if value:
            return value

    except Exception:
        pass

    return os.getenv(
        "GEMINI_API_KEY",
        "",
    )


def gemini_status():

    return {
        "configured":
            bool(
                api_key()
                and genai is not None
            ),

        "sdk_installed":
            genai is not None,
    }


def client():

    if genai is None:

        raise RuntimeError(
            "Cannot import google-genai. "
            "Check requirements.txt and redeploy the Streamlit app."
        )

    key = api_key()

    if not key:

        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add it in Streamlit Secrets."
        )

    return genai.Client(
        api_key=key
    )


def split_sections(
    text,
    max_chars=6000,
):

    paragraphs = [
        p.strip()
        for p in re.split(
            r"\n\s*\n",
            text,
        )
        if p.strip()
    ]

    sections = []

    current = ""

    for paragraph in paragraphs:

        if len(paragraph) <= max_chars:

            candidate = (
                f"{current}\n\n{paragraph}".strip()
                if current
                else paragraph
            )

            if len(candidate) <= max_chars:

                current = candidate

            else:

                sections.append(
                    current
                )

                current = paragraph

            continue

        sentences = re.split(
            r"(?<=[.!?])\s+",
            paragraph,
        )

        for sentence in sentences:

            candidate = (
                f"{current} {sentence}".strip()
                if current
                else sentence
            )

            if len(candidate) <= max_chars:

                current = candidate

            else:

                if current:

                    sections.append(
                        current
                    )

                current = sentence

    if current:

        sections.append(
            current
        )

    return sections


def prompt_for(
    section,
    style,
    preserve_citations,
):

    preserve_rule = (

        "Preserve citation markers, URLs, reference numbers, names, dates, "
        "statistics, formulas and technical terminology."

        if preserve_citations

        else

        "Do not remove factual details or citations."
    )

    return f"""
Rewrite the passage for clarity, readability, and natural expression.

Writing style: {style}

Requirements:
- Preserve the original meaning.
- Preserve factual claims.
- Do not invent facts.
- Do not invent citations, references, quotations or statistics.
- {preserve_rule}
- Improve awkward wording and sentence structure.
- Use natural variation in sentence length.
- Avoid unnecessary repetition.
- Do not add an introduction or conclusion that was not present.
- Return ONLY the rewritten passage.
- Do not discuss these instructions.
- Do not attempt to bypass or defeat AI-detection systems.

PASSAGE:
{section}
""".strip()


def is_changed_enough(
    original,
    rewritten,
):

    a = re.sub(
        r"\s+",
        " ",
        original.strip().lower(),
    )

    b = re.sub(
        r"\s+",
        " ",
        rewritten.strip().lower(),
    )

    if not b:
        return False

    if a == b:
        return False

    similarity = SequenceMatcher(
        None,
        a,
        b,
    ).ratio()

    return similarity < 0.97


def humanize_document(
    text,
    style="Academic and formal",
    preserve_citations=True,
    model="gemini-3.8-flash",
):

    ai = client()

    sections = split_sections(
        text
    )

    if not sections:

        raise ValueError(
            "No readable text was supplied."
        )

    output = []

    unchanged = 0

    failures = []

    for index, section in enumerate(
        sections,
        start=1,
    ):

        try:

            response = ai.models.generate_content(
                model=model,
                contents=prompt_for(
                    section,
                    style,
                    preserve_citations,
                ),
            )

            rewritten = (
                getattr(
                    response,
                    "text",
                    "",
                )
                or ""
            ).strip()

            if not rewritten:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            if is_changed_enough(
                section,
                rewritten,
            ):

                output.append(
                    rewritten
                )

            else:

                output.append(
                    section
                )

                unchanged += 1

        except Exception as exc:

            output.append(
                section
            )

            failures.append(
                f"Section {index}: {exc}"
            )

    notes = [

        f"Processed {len(sections)} section(s).",

        f"{unchanged} section(s) were left unchanged because "
        "the returned text was too similar to the original.",
    ]

    if failures:

        notes.append(
            "Some sections could not be rewritten and were preserved:\n"
            + "\n".join(failures)
        )

    notes.append(
        "No Turnitin or external AI-detector score is generated. "
        "No particular detector result is guaranteed."
    )

    return {

        "text":
            "\n\n".join(
                output
            ).strip(),

        "notes":
            "\n".join(
                notes
            ),
    }
