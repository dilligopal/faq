"""
app.py
Flask entry point for the FAQ Chatbot backend.
Exposes POST /api/chat with 4-step response pipeline:
  1. FAQ fuzzy match   (faq_service)
  2. Wikipedia search  (wiki_service)
  3. Hugging Face AI   (ai_service)
  4. Final fallback message
"""

import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from faq_service  import search_faq
from wiki_service import search_wikipedia
from ai_service   import query_ai

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()
PORT = int(os.getenv("PORT", 5000))

# ── Flask app setup ───────────────────────────────────────────────────────────
app = Flask(__name__)

# Allow all origins (restrict to your frontend URL in production)
CORS(app, resources={r"/api/*": {"origins": "*"}})


# ── Helpers ───────────────────────────────────────────────────────────────────
def sanitise(text: str) -> str:
    """Strip HTML tags, collapse whitespace, cap length."""
    text = re.sub(r"<[^>]+>", "", text)   # remove HTML
    text = re.sub(r"\s+", " ", text)       # collapse spaces
    return text.strip()[:500]


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "FAQ Chatbot API is running",
        "version": "1.0.0",
        "endpoints": {"chat": "POST /api/chat"},
    })


# ── Main chat route ───────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        body = request.get_json(silent=True) or {}
        raw  = body.get("message", "")

        # ── Validation ─────────────────────────────────────────────────────
        if not raw or not str(raw).strip():
            return jsonify({
                "success": False,
                "source":  "error",
                "answer":  "Please type a question before sending.",
                "meta":    {},
            }), 400

        message = sanitise(str(raw))

        if not message:
            return jsonify({
                "success": False,
                "source":  "error",
                "answer":  "Your message appears to be empty. Please try again.",
                "meta":    {},
            }), 400

        print(f"[Chat] Incoming: \"{message}\"")

        # ── Step 1: FAQ fuzzy match ─────────────────────────────────────────
        faq = search_faq(message)
        if faq["found"]:
            print(f"[Chat] Source: FAQ | Score: {faq['score']} | Q: \"{faq['question']}\"")
            return jsonify({
                "success": True,
                "source":  "faq",
                "answer":  faq["answer"],
                "meta": {
                    "matchedQuestion": faq["question"],
                    "category":        faq["category"],
                    "score":           faq["score"],
                },
            })

        # ── Step 2: Wikipedia fallback ──────────────────────────────────────
        wiki = search_wikipedia(message)
        if wiki["found"]:
            title = wiki["title"]
            print(f"[Chat] Source: Wikipedia | Title: \"{title}\"")
            return jsonify({
                "success": True,
                "source":  "wikipedia",
                "answer":  wiki["answer"],
                "meta": {
                    "wikiTitle": title,
                    "wikiUrl":   f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                },
            })

        # ── Step 3: Hugging Face AI fallback ───────────────────────────────
        ai = query_ai(message)
        if ai["found"]:
            print(f"[Chat] Source: AI | Model: {ai['model']}")
            return jsonify({
                "success": True,
                "source":  "ai",
                "answer":  ai["answer"],
                "meta":    {"model": ai["model"]},
            })

        # ── Step 4: Final fallback ──────────────────────────────────────────
        print("[Chat] Source: Fallback")
        return jsonify({
            "success": False,
            "source":  "fallback",
            "answer":  "Sorry, I couldn't find a reliable answer for that question. Try rephrasing it.",
            "meta":    {},
        })

    except Exception as exc:
        print(f"[Chat] Unexpected error: {exc}")
        return jsonify({
            "success": False,
            "source":  "error",
            "answer":  "An internal error occurred. Please try again in a moment.",
            "meta":    {"error": str(exc)},
        }), 500


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("─" * 48)
    print(f"  FAQ Chatbot (Python/Flask) on port {PORT}")
    print(f"  Health:   http://localhost:{PORT}/")
    print(f"  Chat:     POST http://localhost:{PORT}/api/chat")
    print("─" * 48)
    app.run(host="0.0.0.0", port=PORT, debug=True)
