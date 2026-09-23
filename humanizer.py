import os
import streamlit as st
import google.generativeai as genai


def get_api_key():
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        return os.getenv("GOOGLE_API_KEY")


def humanize_text(text):

    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not configured"
        )

    genai.configure(
        api_key=api_key
    )

    model = genai.GenerativeModel(
        "gemini-1.5-flash"
    )

    prompt = f"""
Rewrite the following text so it sounds naturally human-written.

Requirements:
- Preserve meaning
- Keep facts unchanged
- Improve readability
- Vary sentence structure
- Remove repetitive AI wording
- Do not summarize
- Do not shorten

TEXT:

{text}
"""

    response = model.generate_content(
        prompt
    )

    return response.text
