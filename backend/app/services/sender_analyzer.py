import re

SUSPICIOUS_TLDS = {"xyz", "top", "click", "zip", "ru", "cn", "tk", "ml", "ga", "cf", "gq", "loan", "work", "bid", "date", "men", "download", "review", "stream", "trade", "webcam"}
IMPERSONATION_WORDS = ["security-alert", "verify", "login", "support-", "help-desk", "no-reply", "donotreply", "account", "service", "team", "admin", "update", "confirm", "notification", "alert", "secure", "banking", "customercare"]
TRUSTED_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "protonmail.com", "aol.com", "mail.com", "zoho.com", "yandex.com", "github.com", "gitlab.com", "bitbucket.org", "slack.com", "discord.com", "teams.microsoft.com", "zoom.us", "notion.so", "figma.com", "miro.com", "atlassian.net", "asana.com", "trello.com", "google.com", "microsoft.com", "apple.com", "amazon.com", "netflix.com", "spotify.com", "linkedin.com", "twitter.com", "facebook.com", "instagram.com", "reddit.com"}


def analyze_sender(sender: str | None) -> dict:
    sender = (sender or "").lower().strip()
    match = re.search(r"@([a-z0-9.-]+)", sender)
    domain = match.group(1) if match else ""
    tld = domain.rsplit('.', 1)[-1] if '.' in domain else ""
    local_part = sender.split("@")[0] if "@" in sender else ""

    reasons = []
    risk = 0

    if tld in SUSPICIOUS_TLDS:
        reasons.append("Sender uses a suspicious top-level domain")
        risk += 10

    # A domain that is a trusted base or a subdomain of one (app.asana.com,
    # mail.google.com) is inside a brand the operator already trusts: only the
    # brand's own registrars can put anything under it, so suffix-matching is
    # safe against attacker-controlled lookalikes. Penalising these is a
    # false-positive class on ordinary enterprise mail.
    # Suffix stuffing (google.com.attacker.com) does NOT match, because the
    # check compares against the trusted base itself, not a bare brand word.
    within_trusted_brand = domain in TRUSTED_DOMAINS or any(
        domain.endswith("." + d) for d in TRUSTED_DOMAINS
    )

    matched_words = [w for w in IMPERSONATION_WORDS if w in domain]
    if matched_words and not within_trusted_brand:
        reasons.append(f"Sender domain contains impersonation keywords: {', '.join(matched_words[:3])}")
        risk += 10

    trusted_base = any(sender.endswith(f"@{d}") for d in TRUSTED_DOMAINS)

    # Brand impersonation: a trusted brand name appearing as a LABEL in a
    # domain that is not inside that brand's own hierarchy
    # (google-secure.com, paypal-login.xyz). The previous check matched
    # `domain.endswith("." + trusted)`, which can only ever be true for a real
    # subdomain of the brand -- i.e. the opposite of impersonation, and now
    # suppressed above, so it could never fire at all. Match on whole labels so
    # incidental substrings ("applesauce.com" contains "apple") do not flag.
    brand_labels = {t.split(".")[0] for t in TRUSTED_DOMAINS}
    domain_labels = set(re.split(r"[^a-z0-9]+", domain))
    impersonated = sorted(brand_labels & domain_labels)
    if impersonated and not within_trusted_brand:
        reasons.append(f"Brand name used outside its own domain: {', '.join(impersonated[:3])}")
        risk += 8

    if local_part and re.search(r"(admin|support|service|help|info|contact|team|noreply|donotreply)", local_part) and tld in SUSPICIOUS_TLDS:
        reasons.append(f"Suspicious sender pattern: '{local_part}@{domain}' mimics a legitimate address")
        risk += 5

    if domain.count(".") >= 3:
        reasons.append(f"Excessive subdomains in sender domain: {domain}")
        risk += 5

    return {
        "sender": sender,
        "domain": domain,
        "risk": min(30, risk),
        "reasons": reasons,
    }
