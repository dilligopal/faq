"""
wiki_service.py
Queries the free Wikipedia REST API for a plain-text summary.
Returns {"found": False} for disambiguation pages, empty results,
or any network/API failure — never raises an exception to the caller.
"""

import requests

SEARCH_URL  = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
TIMEOUT     = 5  # seconds

# Phrases that indicate a useless disambiguation or stub page
WEAK_PHRASES = [
    "may refer to",
    "can refer to",
    "disambiguation",
    "this article is about",
]


def _is_weak(summary: str) -> bool:
    if not summary or len(summary.strip()) < 40:
        return True
    low = summary.lower()
    return any(phrase in low for phrase in WEAK_PHRASES)


def _search_title(query: str) -> str | None:
    """Use Wikipedia OpenSearch to find the best matching page title."""
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 3,
        "namespace": 0,
        "format": "json",
    }
    resp = requests.get(SEARCH_URL, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    titles = data[1] if len(data) > 1 else []
    return titles[0] if titles else None


def _fetch_summary(title: str) -> str | None:
    """Fetch the plain-text extract for a Wikipedia page title."""
    url = f"{SUMMARY_URL}/{requests.utils.quote(title)}"
    resp = requests.get(
        url,
        timeout=TIMEOUT,
        headers={"User-Agent": "FAQChatbot/1.0 (educational project)"},
    )
    resp.raise_for_status()
    return resp.json().get("extract")


def search_wikipedia(user_message: str) -> dict:
    """
    Search Wikipedia for user_message.

    Returns:
        {"found": True,  "answer": str, "title": str}
        or {"found": False}
    """
    try:
        title = _search_title(user_message)
        if not title:
            return {"found": False}

        summary = _fetch_summary(title)
        if not summary or _is_weak(summary):
            return {"found": False}

        # Trim to the first 3 sentences for conciseness
        sentences = summary.split(". ")
        trimmed = (
            ". ".join(sentences[:3]) + "."
            if len(sentences) > 3
            else summary
        )

        return {"found": True, "answer": trimmed, "title": title}

    except Exception as exc:
        print(f"[WikiService] Error: {exc}")
        return {"found": False}
