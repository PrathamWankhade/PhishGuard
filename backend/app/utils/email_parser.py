from email import policy
from email.parser import Parser
from email.utils import getaddresses
import re

URL_RE = re.compile(r"https?://[^\s<>\")\]]+|www\.[^\s<>\")\]]+", re.IGNORECASE)

MAX_BODY_CHARS = 50000


def _extract_urls(text: str) -> list[str]:
    if not text:
        return []
    return [u.rstrip(".,;:!?'\"") for u in URL_RE.findall(text)]


def parse_raw_email(raw_email: str) -> dict:
    """Standards-aware MIME parsing. Never raises on malformed input."""
    if not raw_email:
        return {"sender": "", "subject": "", "body": "", "urls": [],
                "attachments": [], "errors": ["empty message"]}
    if len(raw_email) > 2_000_000:
        return {"sender": "", "subject": "", "body": "", "urls": [],
                "attachments": [], "errors": ["message exceeds 2MB limit"]}
    errors: list[str] = []
    try:
        message = Parser(policy=policy.default).parsestr(raw_email)
    except Exception as e:
        return {"sender": "", "subject": "", "body": raw_email[:MAX_BODY_CHARS],
                "urls": _extract_urls(raw_email), "attachments": [],
                "errors": [f"header parse failed: {e}"]}
    try:
        sender = str(message.get("from", "") or "")
        # Normalize to bare address when present.
        addrs = getaddresses([sender])
        if addrs and addrs[0][1]:
            sender = addrs[0][1]
        subject = str(message.get("subject", "") or "")
        reply_to = str(message.get("reply-to", "") or "")
        return_path = str(message.get("return-path", "") or "")

        body = ""
        attachments: list[dict] = []
        try:
            if message.is_multipart():
                for part in message.walk():
                    if part.is_multipart():
                        continue
                    disp = part.get_content_disposition() or ""
                    ctype = part.get_content_type()
                    if disp == "attachment":
                        try:
                            payload = part.get_payload(decode=True) or b""
                        except Exception:
                            payload = b""
                        attachments.append({
                            "filename": part.get_filename() or "",
                            "content_type": ctype,
                            "size_bytes": len(payload),
                        })
                    elif ctype == "text/plain" and not body:
                        try:
                            body = part.get_content()
                        except Exception as e:
                            errors.append(f"body decode failed: {e}")
                if not body:
                    # Fall back to first text part (e.g. HTML-only mail).
                    for part in message.walk():
                        if part.get_content_type().startswith("text/"):
                            try:
                                body = part.get_content()
                                break
                            except Exception:
                                continue
            else:
                try:
                    body = message.get_content()
                except Exception:
                    body = message.get_payload(decode=True)
                    if isinstance(body, bytes):
                        body = body.decode("utf-8", errors="ignore")
        except Exception as e:
            errors.append(f"body extraction failed: {e}")
            body = ""

        if not isinstance(body, str):
            body = str(body or "")
        body = body[:MAX_BODY_CHARS]
        return {
            "sender": sender,
            "subject": subject,
            "reply_to": reply_to,
            "return_path": return_path,
            "body": body,
            "urls": _extract_urls(body + "\n" + subject),
            "attachments": attachments,
            "errors": errors,
        }
    except Exception as e:
        return {"sender": "", "subject": "", "body": raw_email[:MAX_BODY_CHARS],
                "urls": _extract_urls(raw_email), "attachments": [],
                "errors": [f"parse failed: {e}"]}
