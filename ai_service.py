"""
ai_service.py
Calls the Hugging Face free Inference API as a last-resort fallback.
API key is read from .env — never hardcoded or exposed to the frontend.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HF_MODEL   = os.getenv("HUGGINGFACE_MODEL", "google/flan-t5-large")
HF_URL     = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
TIMEOUT    = 15  # seconds — free tier can be slow


def _build_prompt(user_message: str) -> str:
    return (
        "You are a helpful customer support FAQ assistant. "
        "Answer the following customer question concisely in 1-2 sentences. "
        "The customer may use spelling mistakes or informal language — understand and answer correctly. "
        "Do NOT make up facts. If unsure, say you are not sure and suggest contacting support.\n\n"
        f'Customer question: "{user_message}"\n\nAnswer:'
    )


def query_ai(user_message: str) -> dict:
    """
    Query the Hugging Face Inference API.

    Returns:
        {"found": True,  "answer": str, "model": str}
        or {"found": False}
    """
    if not HF_API_KEY or HF_API_KEY == "your_huggingface_token_here":
        print("[AIService] No Hugging Face API key configured. Skipping.")
        return {"found": False}

    try:
        payload = {
            "inputs": _build_prompt(user_message),
            "parameters": {
                "max_new_tokens": 120,
                "temperature": 0.5,
                "do_sample": True,
                "return_full_text": False,
            },
        }
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }

        resp = requests.post(HF_URL, json=payload, headers=headers, timeout=TIMEOUT)

        if resp.status_code == 503:
            print("[AIService] Model loading (503). Skipping.")
            return {"found": False}

        if resp.status_code == 401:
            print("[AIService] Invalid API key (401). Check your .env file.")
            return {"found": False}

        resp.raise_for_status()
        data = resp.json()

        # Response is a list: [{"generated_text": "..."}]
        ai_answer = None
        if isinstance(data, list) and data and "generated_text" in data[0]:
            ai_answer = data[0]["generated_text"].strip()
        elif isinstance(data, dict) and "generated_text" in data:
            ai_answer = data["generated_text"].strip()

        if not ai_answer or len(ai_answer) < 5:
            return {"found": False}

        # Strip echoed "Answer:" prefix if present
        if ai_answer.lower().startswith("answer:"):
            ai_answer = ai_answer[7:].strip()

        return {"found": True, "answer": ai_answer, "model": HF_MODEL}

    except Exception as exc:
        print(f"[AIService] Error: {exc}")
        return {"found": False}
