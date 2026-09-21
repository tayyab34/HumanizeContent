import streamlit as st

st.title("APP REPLACED SUCCESSFULLY")

main_text = "Test text loaded successfully"

st.text_area(
    "Document Preview",
    main_text,
    height=300
)
