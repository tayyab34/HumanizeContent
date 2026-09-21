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

document_text = ""

if uploaded_file:

    try:
        document_text = uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )
    except:
        document_text = ""

    st.subheader("Document Preview")

    st.text_area(
        "Document Preview",
        value=document_text[:12000] if document_text else "",
        height=300
    )

    if st.button("Analyze"):

        st.success("Document loaded successfully")

        st.write(
            f"Characters: {len(document_text)}"
        )
