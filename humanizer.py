import re


def humanize_text(text):

    text = re.sub(
        r"\btherefore\b",
        "so",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bmoreover\b",
        "also",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bfurthermore\b",
        "besides",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bin conclusion\b",
        "to sum up",
        text,
        flags=re.IGNORECASE
    )

    return text
