import streamlit as st

st.set_page_config(
    page_title="AI Humanizer + Plagiarism Checker",
    layout="wide"
)

st.title("AI Humanizer + Plagiarism Checker")

uploaded_file = st.file_uploader(
    "Upload document",
    type=["txt", "pdf", "docx"]
)

# IMPORTANT: define main_text before using it
main_text = ""

if uploaded_file is not None:

    try:
        if uploaded_file.name.endswith(".txt"):
            main_text = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )
        else:
            # Placeholder for PDF/DOCX extraction
            main_text = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

    except Exception as ex:
        st.error(f"Error reading file: {ex}")
        main_text = ""

    st.subheader("Document Preview")

    st.text_area(
        "Document Preview",
        main_text[:12000],
        height=300,
        label_visibility="visible"
    )

    if st.button("Analyze"):

        st.success("Document loaded successfully")

        st.write(
            f"Characters: {len(main_text)}"
        )

        st.write(
            f"Words: {len(main_text.split())}"
        )
