"""Business-email-compromise / fraud signals.

Keyword-pattern evidence only — never a standalone verdict. Findings feed
the decision engine as capped risk points plus human-readable signals.
"""
import re

FINANCIAL_PATTERNS = [
    r"wire transfer", r"bank transfer", r"gift ?cards?", r"cryptocurrency",
    r"\bbitcoin\b", r"routing number", r"invoice.*(overdue|payment)",
    r"update.*payment (details|method|information)", r"change.*bank(ing)? (details|account)",
]

EXECUTIVE_PATTERNS = [
    r"\bceo\b", r"\bcfo\b", r"\bboard\b", r"executive", r"managing director",
    r"i am (the|your) (ceo|cfo|boss|manager)",
]

SECRECY_PATTERNS = [
    r"keep (this |it )?confidential", r"do not (tell|inform|discuss)",
    r"between (us|you and me)", r"urgent.*secret", r"handle (this )?discreetly",
]

CREDENTIAL_PATTERNS = [
    r"verif\w+.*(password|account|login|credential)",
    r"(password|credential).*(expir\w+|suspend|block|deactivat)",
    r"click.*(verif\w+|confirm|update).*(account|password|login)",
]


def analyze_bec(email_text: str, sender: str = "") -> dict:
    text = (email_text or "").lower()
    reasons: list[str] = []
    risk = 0

    if any(re.search(p, text) for p in FINANCIAL_PATTERNS):
        reasons.append("Financial-fraud pattern: payment / transfer / invoice request")
        risk += 6
    if any(re.search(p, text) for p in EXECUTIVE_PATTERNS):
        reasons.append("Possible executive impersonation: senior-title language")
        risk += 5
    if any(re.search(p, text) for p in SECRECY_PATTERNS):
        reasons.append("Secrecy pressure: asks recipient to keep the request quiet")
        risk += 5
    if any(re.search(p, text) for p in CREDENTIAL_PATTERNS):
        reasons.append("Credential-harvesting pattern: verification / suspension lure")
        risk += 6

    return {"reasons": reasons, "risk": min(15, risk)}
