"""
faq_service.py
Loads faq.json and uses rapidfuzz for fuzzy matching across
question and keywords fields. Handles typos, short forms,
and badly typed questions like "wat is ur timing".
"""

import json
import os
from rapidfuzz import fuzz, process

# ── Load FAQ data once at import time ────────────────────────────────────────
_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "faq.json")

with open(_DATA_PATH, encoding="utf-8") as f:
    FAQ_DATA = json.load(f)

# ── Build a flat search corpus ────────────────────────────────────────────────
# Each entry maps a searchable string → original FAQ item.
# We index the question AND every keyword so either can trigger a match.
_CORPUS: list[tuple[str, dict]] = []

for item in FAQ_DATA:
    # Add the question itself
    _CORPUS.append((item["question"].lower(), item))
    # Add every keyword
    for kw in item.get("keywords", []):
        _CORPUS.append((kw.lower(), item))

# Extract just the strings for rapidfuzz
_STRINGS = [pair[0] for pair in _CORPUS]

# ── Match threshold ───────────────────────────────────────────────────────────
# rapidfuzz scores 0–100.  We require ≥ 60 to count as a match.
# token_set_ratio handles word-order differences and partial overlaps well.
THRESHOLD = 60


def search_faq(user_message: str) -> dict:
    """
    Search the FAQ corpus for the best fuzzy match.

    Returns:
        {
            "found": True,
            "answer": str,
            "question": str,
            "category": str,
            "score": float
        }
        or {"found": False}
    """
    if not user_message or not user_message.strip():
        return {"found": False}

    query = user_message.strip().lower()

    # token_set_ratio is robust against reordered words and partial matches
    result = process.extractOne(
        query,
        _STRINGS,
        scorer=fuzz.token_set_ratio,
        score_cutoff=THRESHOLD,
    )

    if result is None:
        return {"found": False}

    matched_string, score, index = result
    item = _CORPUS[index][1]

    return {
        "found": True,
        "answer": item["answer"],
        "question": item["question"],
        "category": item["category"],
        "score": round(score, 2),
        "id": item["id"],
    }
