
import io, hashlib
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Document Integrity RAG", layout="wide")
st.title("Document Integrity RAG (Streamlit)")

def read_text(uploaded_file):
    try:
        return uploaded_file.read().decode("utf-8", errors="ignore")
    except:
        return ""

def similarity(a, b):
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return round(len(wa & wb) / len(wa | wb) * 100, 2)

doc1 = st.file_uploader("Upload Document", type=["txt","md"])
doc2 = st.file_uploader("Upload Reference Document", type=["txt","md"])

if doc1 and doc2:
    t1 = read_text(doc1)
    t2 = read_text(doc2)

    score = similarity(t1, t2)

    st.metric("Similarity %", score)

    st.subheader("Document Hash")
    st.code(hashlib.sha256(t1.encode()).hexdigest())

    st.subheader("Document Preview")
    st.text_area("Document", t1[:5000], height=250)
    st.text_area("Reference", t2[:5000], height=250)
