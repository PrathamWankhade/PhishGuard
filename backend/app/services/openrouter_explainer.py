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
_ai_semaphore = None  # created lazily so import never validates config


def _get_semaphore() -> threading.BoundedSemaphore:
    global _ai_semaphore
    if _ai_semaphore is None:
        _ai_semaphore = threading.BoundedSemaphore(_semaphore_size())
    return _ai_semaphore


def _budget_allows() -> bool:
    """Daily spending cap on SUBMITTED provider calls. Returns True and
    records usage, or False. Raises on misconfiguration (loud, never silent).
    """
    global _ai_day, _ai_used_today
    raw = os.environ.get("AI_DAILY_BUDGET", "500")
    try:
        cap = int(raw)
    except ValueError:
        raise RuntimeError(f"Invalid AI_DAILY_BUDGET={raw!r}; expected a non-negative integer.")
    if cap < 0:
        raise RuntimeError(f"Invalid AI_DAILY_BUDGET={raw!r}; expected a non-negative integer.")
    # cap == 0 is valid: zero paid calls allowed (hard local-only).
    today = str(date.today())
    with _ai_lock:
        if today != _ai_day:
            _ai_day, _ai_used_today = today, 0
        if _ai_used_today >= cap:
            return False
        _ai_used_today += 1
        return True


def _semaphore_size() -> int:
    raw = os.environ.get("AI_MAX_CONCURRENT", "4")
    try:
        n = int(raw)
    except ValueError:
        raise RuntimeError(f"Invalid AI_MAX_CONCURRENT={raw!r}; expected a positive integer.")
    if n <= 0:
        raise RuntimeError(f"Invalid AI_MAX_CONCURRENT={raw!r}; expected a positive integer.")
    return n

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
    # Order: concurrency slot FIRST, budget reservation only for submitted
    # calls. A saturated provider must not consume the daily budget.
    sem = _get_semaphore()
    if not sem.acquire(blocking=False):
        return None  # provider saturated: degrade, never queue unboundedly
    try:
        if not _budget_allows():
            return None  # daily provider budget exhausted: stay local-only
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
        sem.release()
