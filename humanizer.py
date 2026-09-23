import os
import streamlit as st
from google import genai


def get_api_key():

    try:
        key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        key = os.getenv("GOOGLE_API_KEY")

    return key


def humanize_text(text):

    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not configured"
        )

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
Rewrite the text so it reads naturally and professionally.

Rules:

- Preserve meaning
- Human writing style
- Vary sentence structure
- Remove repetitive AI wording
- Keep facts unchanged
- Do not summarize
- Do not shorten

Text:

{text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
