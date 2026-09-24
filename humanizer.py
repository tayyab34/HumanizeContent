import os
import google.generativeai as genai


def gemini_status():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "configured": False,
            "message": "GEMINI_API_KEY is not configured."
        }

    return {
        "configured": True,
        "message": "Gemini API is configured."
    }


def humanize_document(text):
    if not text or not text.strip():
        return ""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        "gemini-2.0-flash"
    )

    prompt = f"""
Rewrite the following text to make it clearer,
more natural, and easier to read while preserving
the original meaning.

Do not add new facts.

Text:

{text}
"""

    response = model.generate_content(prompt)

    if not response or not response.text:
        raise RuntimeError(
            "Gemini did not return any text."
        )

    return response.text
