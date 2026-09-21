import re
from typing import List

import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


MODEL_NAME = "google/flan-t5-small"


@st.cache_resource
def load_humanizer_model():
    """
    Load the local FLAN-T5 model once.
    """

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME
    )

    return tokenizer, model


def split_sentences(text: str) -> List[str]:
    """
    Split text into manageable sentences.
    """

    return [
        x.strip()
        for x in re.split(
            r"(?<=[.!?])\s+",
            text
        )
        if x.strip()
    ]


def humanize_sentence(
    sentence: str,
    tokenizer,
    model
) -> str:

    prompt = f"""
Rewrite the following text in natural, clear,
human-sounding English.

Keep the original meaning.
Do not add new facts.
Do not remove important information.
Avoid unnecessary formal language.
Use natural sentence structure.

Text:
{sentence}

Rewritten text:
""".strip()

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=120,
        num_beams=4,
        temperature=0.8,
        do_sample=True,
        repetition_penalty=1.15,
        no_repeat_ngram_size=3
    )

    result = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    ).strip()

    if not result:
        return sentence

    return result


def humanize_text(
    text: str,
    max_sentences: int = 100
) -> str:
    """
    Rewrite document text sentence-by-sentence.
    """

    if not text:
        return ""

    tokenizer, model = load_humanizer_model()

    sentences = split_sentences(text)

    if not sentences:
        return text

    sentences = sentences[:max_sentences]

    rewritten = []

    progress = st.progress(0)

    total = len(sentences)

    for i, sentence in enumerate(sentences):

        try:

            result = humanize_sentence(
                sentence,
                tokenizer,
                model
            )

            rewritten.append(result)

        except Exception:

            # Keep original sentence if generation fails
            rewritten.append(sentence)

        progress.progress(
            (i + 1) / total
        )

    progress.empty()

    return " ".join(rewritten)
