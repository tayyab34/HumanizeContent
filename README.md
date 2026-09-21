# 📄 Humanize RAG - AI Content Humanizer + Plagiarism Checker

A Streamlit-based RAG application that can:

- Upload PDF, DOCX and TXT files
- Extract document text
- Search web sources using SerpAPI
- Generate semantic embeddings
- Build a FAISS vector index
- Compare uploaded content with web search results
- Detect potentially similar web passages
- Rewrite content using a local FLAN-T5 model
- Download the rewritten content

---

# Features

## 1. Document Upload

Supported files:

- PDF
- DOCX
- TXT

The application uses your existing:

```text
extractors.py
