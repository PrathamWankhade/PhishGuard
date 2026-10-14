import os
import json
import threading
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

AI_ENABLED = os.environ.get("AI_EXPLANATIONS_ENABLED", "true").lower() not in ("0", "false", "no")

# Cost/abuse controls for the paid external provider (single-instance).
# - AI_DAILY_BUDGET: max provider calls per calendar day (default 500).
# - AI_MAX_CONCURRENT: max simultaneous provider calls (default 4).
_ai_lock = threading.Lock()
_ai_day = str(date.today())
_ai_used_today = 0
_ai_semaphore = threading.BoundedSemaphore(int(os.environ.get("AI_MAX_CONCURRENT", "4")))


def _budget_allows() -> bool:
    """Daily spending cap. Returns True and records usage, or False."""
    global _ai_day, _ai_used_today
    try:
        cap = int(os.environ.get("AI_DAILY_BUDGET", "500"))
    except ValueError:
        cap = 500
    today = str(date.today())
    with _ai_lock:
        if today != _ai_day:
            _ai_day, _ai_used_today = today, 0
        if _ai_used_today >= cap:
            return False
        _ai_used_today += 1
        return True

# NOTE: the client is created lazily inside _get_client(), never at import
# time. Constructing OpenAI() requires credentials, and importing this module
# (e.g. during pytest collection in CI) must never fail for lack of keys.
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            timeout=10.0,
            max_retries=1,
        )
    return _client

MODEL = "meta-llama/llama-3.3-70b-instruct"

SYSTEM_PROMPT = """You are a cybersecurity phishing analyst. Given an email and its classification result, explain why it was flagged. Return exactly 3 short bullet points in simple language covering relevant phishing indicators such as urgency, credential requests, suspicious links, fake domains, or social engineering tactics. Keep it under 80 words total."""


def generate_ai_explanation(email_text: str, sender: str, prediction: str, confidence: float) -> list[str] | None:
    """Supplementary AI summary. Returns None when disabled/unavailable.

    Privacy: up to 2000 chars of email text are sent to the external provider.
    Set AI_EXPLANATIONS_ENABLED=false or unset OPENROUTER_API_KEY for
    local-only mode (no email content leaves the server).
    """
    if not AI_ENABLED or not os.getenv("OPENROUTER_API_KEY"):
        return None
    if not _budget_allows():
        return None  # daily provider budget exhausted: stay local-only
    if not _ai_semaphore.acquire(blocking=False):
        return None  # provider saturated: degrade, never queue unboundedly
    try:
        client = _get_client()
        prompt = f"Prediction: {prediction}\nConfidence: {confidence}%\nSender: {sender}\n\nEmail:\n{email_text[:2000]}"

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        text = response.choices[0].message.content.strip()
        reasons = [line.strip("•- ") for line in text.split("\n") if line.strip()]
        return reasons

    except Exception as error:
        print("OpenRouter error:", error)
        return ["AI explanation unavailable."]
    finally:
        _ai_semaphore.release()
