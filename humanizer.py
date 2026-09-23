import streamlit as st
from google import genai

def humanize_text(text):

    client = genai.Client(
        api_key=st.secrets["GOOGLE_API_KEY"]
    )

    prompt = f"""
Rewrite the following text so it sounds naturally human-written.

Requirements:
- Preserve meaning
- Improve readability
- Reduce AI-like phrasing
- Keep facts unchanged

TEXT:
{text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
