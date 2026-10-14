"""Header authentication + reply-path mismatch signals.

Local-only analysis of message headers supplied by the caller/parser.
We never fetch external reputation data here. Findings distinguish:
- trusted authentication results (parsed Authentication-Results header),
- reply-path mismatches (From vs Reply-To / Return-Path),
which the text classifier cannot see.
"""
import re


def _domain_of(addr: str) -> str:
    m = re.search(r"@([a-z0-9.-]+)", (addr or "").lower())
    return m.group(1).strip().rstrip(".") if m else ""


def analyze_auth(
    sender: str = "",
    reply_to: str = "",
    return_path: str = "",
    auth_results: str = "",
) -> dict:
    reasons: list[str] = []
    risk = 0

    sender_domain = _domain_of(sender)
    reply_domain = _domain_of(reply_to)
    bounce_domain = _domain_of(return_path)

    if reply_to and reply_domain and sender_domain and reply_domain != sender_domain:
        reasons.append(
            f"Reply-To domain ({reply_domain}) differs from sender domain ({sender_domain})"
        )
        risk += 8

    if return_path and bounce_domain and sender_domain and bounce_domain != sender_domain:
        reasons.append(
            f"Return-Path domain ({bounce_domain}) differs from sender domain ({sender_domain})"
        )
        risk += 5

    if auth_results:
        ar = auth_results.lower()
        for method in ("spf", "dkim", "dmarc"):
            m = re.search(rf"{method}\s*=\s*(pass|fail|softfail|neutral|none|temperror|permerror)", ar)
            if m:
                verdict = m.group(1)
                if verdict in ("fail", "softfail", "permerror"):
                    reasons.append(f"Email authentication failed: {method}={verdict}")
                    risk += 8
                elif verdict == "pass":
                    reasons.append(f"Email authentication passed: {method}=pass")

    return {"reasons": reasons, "risk": min(20, risk)}
