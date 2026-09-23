import html
import re

from urllib.parse import quote_plus

import requests


USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; HumanizeContent/1.0; "
    "+https://streamlit.io/)"
)


def search_web(
    query,
    max_results=8,
):

    """
    Uses DuckDuckGo's HTML search endpoint
    for lightweight source discovery.

    This is only source discovery.
    Returned pages should be opened and checked
    before relying on their contents.
    """

    query = query.strip()

    if not query:
        return []

    url = (
        "https://html.duckduckgo.com/html/"
        f"?q={quote_plus(query)}"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=20,
    )

    response.raise_for_status()

    page = response.text

    results = []

    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.I | re.S,
    )

    for match in pattern.finditer(
        page
    ):

        href = html.unescape(
            match.group(1)
        )

        title = re.sub(
            r"<.*?>",
            "",
            html.unescape(
                match.group(2)
            ),
        ).strip()

        if not title or not href:
            continue

        if href.startswith("//"):

            href = "https:" + href

        results.append(
            {
                "title": title,
                "url": href,
            }
        )

        if len(results) >= max_results:
            break

    return results


def format_search_results(
    results
):

    if not results:

        return (
            "No search results were returned."
        )

    lines = []

    for item in results:

        title = (
            item["title"]
            .replace("[", "")
            .replace("]", "")
        )

        url = item["url"]

        lines.append(
            f"- [{title}]({url})"
        )

    return "\n".join(
        lines
    )
