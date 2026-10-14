import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

AI_ENABLED = os.environ.get("AI_EXPLANATIONS_ENABLED", "true").lower() not in ("0", "false", "no")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    timeout=10.0,
    max_retries=1,
)

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
    try:
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
