import os
import streamlit as st
from dotenv import load_dotenv

from extractors import (
    extract_text_from_file,
    supported_extensions
)

from plagiarism import (
    CopyleaksClient,
    CopyleaksError,
    detect_ai_text,
    parse_ai_result,
    analyze_with_copyleaks
)

from humanizer import (
    humanize_document,
    gemini_status
)

from web_search import (
    search_web,
    format_search_results
)


load_dotenv()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI & Plagiarism Checker",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #666;
        margin-bottom: 25px;
    }

    .result-box {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">'
    'AI & Plagiarism Checker'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Check documents for plagiarism and AI-generated content.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Copyleaks")

    copyleaks_email = os.getenv(
        "COPYLEAKS_EMAIL",
        ""
    )

    copyleaks_key = os.getenv(
        "COPYLEAKS_API_KEY",
        ""
    )

    sandbox_default = (
        os.getenv(
            "COPYLEAKS_SANDBOX",
            "true"
        ).lower()
        in ("true", "1", "yes", "y")
    )

    if copyleaks_email:
        st.success("Copyleaks email configured")
    else:
        st.warning(
            "COPYLEAKS_EMAIL is not configured."
        )

    if copyleaks_key:
        st.success("Copyleaks API key configured")
    else:
        st.warning(
            "COPYLEAKS_API_KEY is not configured."
        )

    sandbox = st.checkbox(
        "Sandbox mode",
        value=sandbox_default
    )

    st.caption(
        "Sandbox mode is useful for testing. "
        "Production scans may consume Copyleaks credits."
    )


# ============================================================
# FILE UPLOAD
# ============================================================

st.subheader("Upload Document")

allowed_extensions = supported_extensions()

main_file = st.file_uploader(
    "Choose a file",
    type=allowed_extensions
)


if not main_file:

    st.info(
        "Upload a PDF, DOCX, TXT, or another supported "
        "document to start."
    )

    st.stop()


# ============================================================
# READ FILE
# ============================================================

file_bytes = main_file.getvalue()

filename = main_file.name


# ============================================================
# EXTRACT TEXT
# ============================================================

try:

    extracted_text = extract_text_from_file(
        main_file
    )

except Exception as exc:

    st.error(
        f"Could not extract text from the document: {exc}"
    )

    st.stop()


if not extracted_text:

    st.warning(
        "No text could be extracted from this file."
    )

    st.stop()


# ============================================================
# BASIC INFORMATION
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "File",
        filename
    )

with col2:
    st.metric(
        "Characters",
        len(extracted_text)
    )

with col3:
    st.metric(
        "Words",
        len(extracted_text.split())
    )


# ============================================================
# TABS
# ============================================================

tab_local, tab_copyleaks, tab_rewrite, tab_search, tab_text = (
    st.tabs(
        [
            "Local Similarity",
            "Copyleaks",
            "Rewrite",
            "Source Search",
            "Extracted Text"
        ]
    )
)


# ============================================================
# LOCAL SIMILARITY
# ============================================================

with tab_local:

    st.subheader("Local Similarity")

    reference_files = st.file_uploader(
        "Upload reference files",
        accept_multiple_files=True,
        key="reference_files"
    )

    if st.button(
        "Run Local Similarity",
        key="local_similarity_button"
    ):

        if not reference_files:

            st.warning(
                "Please upload at least one reference file."
            )

        else:

            st.info(
                "Local similarity analysis can be connected "
                "to your existing plagiarism.py implementation."
            )


# ============================================================
# COPYLEAKS
# ============================================================

with tab_copyleaks:

    st.subheader(
        "Copyleaks Plagiarism + AI Detection"
    )

    st.write(
        "Copyleaks requires your account email and API key."
    )

    st.code(
        "COPYLEAKS_EMAIL=your-email@example.com\n"
        "COPYLEAKS_API_KEY=your-api-key",
        language="text"
    )

    if not copyleaks_email or not copyleaks_key:

        st.error(
            "Copyleaks credentials are not configured."
        )

        st.info(
            "Add COPYLEAKS_EMAIL and COPYLEAKS_API_KEY "
            "to your .env file."
        )

    else:

        if st.button(
            "Check Copyleaks",
            key="copyleaks_check"
        ):

            try:

                client = CopyleaksClient(
                    email=copyleaks_email,
                    api_key=copyleaks_key,
                    sandbox=sandbox
                )

                with st.spinner(
                    "Authenticating with Copyleaks..."
                ):

                    client.login()

                st.success(
                    "Copyleaks authentication successful."
                )

            except CopyleaksError as exc:

                st.error(
                    str(exc)
                )

        st.divider()

        # ----------------------------------------------------
        # DIRECT AI TEXT DETECTION
        # ----------------------------------------------------

        st.subheader(
            "AI-Generated Content Detection"
        )

        if len(extracted_text) < 255:

            st.warning(
                f"Copyleaks AI text detection requires at "
                f"least 255 characters. "
                f"Your document has {len(extracted_text)}."
            )

        else:

            if st.button(
                "Check AI Content",
                key="ai_detection_button"
            ):

                try:

                    with st.spinner(
                        "Checking AI-generated content..."
                    ):

                       ai_result = detect_ai_text(
    text=extracted_text,
    email=copyleaks_email,
    api_key=copyleaks_key,
    sandbox=sandbox
)

                    parsed_ai = parse_ai_result(
                        ai_result
                    )

                    ai_percentage = (
                        parsed_ai["ai_probability"]
                    )

                    human_percentage = (
                        parsed_ai["human_probability"]
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if ai_percentage is not None:

                            st.metric(
                                "AI Probability",
                                f"{ai_percentage:.1f}%"
                            )

                        else:

                            st.metric(
                                "AI Probability",
                                "N/A"
                            )

                    with col2:

                        if human_percentage is not None:

                            st.metric(
                                "Human Probability",
                                f"{human_percentage:.1f}%"
                            )

                        else:

                            st.metric(
                                "Human Probability",
                                "N/A"
                            )

                    with st.expander(
                        "View Copyleaks AI Response"
                    ):

                        st.json(
                            ai_result
                        )

                except CopyleaksError as exc:

                    st.error(
                        str(exc)
                    )

                except Exception as exc:

                    st.error(
                        f"Unexpected error: {exc}"
                    )

        st.divider()

        # ----------------------------------------------------
        # FULL DOCUMENT SCAN
        # ----------------------------------------------------

        st.subheader(
            "Full Document Scan"
        )

        st.write(
            "This submits the original file to Copyleaks "
            "for plagiarism and AI detection."
        )

        st.warning(
            "Production document scans are asynchronous "
            "and require a publicly reachable webhook."
        )

        webhook_url = st.text_input(
            "Webhook base URL",
            value=os.getenv(
                "COPYLEAKS_WEBHOOK_URL",
                ""
            ),
            placeholder="https://your-domain.com"
        )

        if st.button(
            "Submit Full Copyleaks Scan",
            key="full_copyleaks_scan"
        ):

            if not sandbox and not webhook_url:

                st.error(
                    "A public HTTPS webhook URL is required "
                    "for production Copyleaks document scans."
                )

            else:

                try:

                    with st.spinner(
                        "Submitting document to Copyleaks..."
                    ):

                        result = analyze_with_copyleaks(
                            file_bytes=file_bytes,
                            filename=filename,
                            webhook_url=webhook_url
                            if webhook_url
                            else "https://example.com",
                            sandbox=sandbox
                        )

                    st.success(
                        "Document submitted successfully."
                    )

                    st.write(
                        "Scan ID:"
                    )

                    st.code(
                        result["scan_id"]
                    )

                    if result.get(
                        "plagiarism_score"
                    ) is not None:

                        st.metric(
                            "Plagiarism Score",
                            f"{result['plagiarism_score']:.2f}%"
                        )

                    st.info(
                        "Final production results are delivered "
                        "through the Copyleaks completion webhook."
                    )

                    with st.expander(
                        "View submission response"
                    ):

                        st.json(
                            result["response"]
                        )

                except CopyleaksError as exc:

                    st.error(
                        str(exc)
                    )

                except Exception as exc:

                    st.error(
                        f"Unexpected error: {exc}"
                    )


# ============================================================
# REWRITE
# ============================================================

with tab_rewrite:

    st.subheader("Rewrite / Humanize")

    if st.button(
        "Rewrite Document",
        key="rewrite_document"
    ):

        try:

            with st.spinner(
                "Rewriting document..."
            ):

                rewritten = humanize_document(
                    extracted_text
                )

            st.text_area(
                "Rewritten Content",
                rewritten,
                height=500
            )

        except Exception as exc:

            st.error(
                f"Rewrite failed: {exc}"
            )


# ============================================================
# SOURCE SEARCH
# ============================================================

with tab_search:

    st.subheader(
        "Search Web Sources"
    )

    search_query = st.text_input(
        "Search query",
        value=""
    )

    if st.button(
        "Search Sources",
        key="search_sources"
    ):

        if not search_query.strip():

            st.warning(
                "Enter a search query."
            )

        else:

            try:

                results = search_web(
                    search_query
                )

                st.markdown(
                    format_search_results(
                        results
                    ),
                    unsafe_allow_html=True
                )

            except Exception as exc:

                st.error(
                    f"Search failed: {exc}"
                )


# ============================================================
# EXTRACTED TEXT
# ============================================================

with tab_text:

    st.subheader(
        "Extracted Text"
    )

    st.text_area(
        "Document Text",
        extracted_text,
        height=600
    )
