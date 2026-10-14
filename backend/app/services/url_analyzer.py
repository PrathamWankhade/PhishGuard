import re
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {"xyz", "top", "click", "zip", "ru", "cn", "tk", "ml", "ga", "cf", "gq", "loan", "work", "bid", "date", "men", "download", "review", "stream", "trade", "webcam"}
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "tiny.cc", "tr.im", "shorturl.at", "cut.ly", "rb.gy", "short.link", "click", "b.link", "cutt.ly", "shorte.st", "adf.ly", "bc.vc"}
PHISHING_PATTERNS = re.compile(r"(credential|authenticate|reset-password|secure-login|banking-verify)", re.IGNORECASE)


def is_homograph(domain: str) -> bool:
    """Detect likely lookalike (homograph) domains.

    Operates on the raw (unicode) hostname: pure-ASCII names are never
    homographs; names with non-ASCII chars are flagged only when a single
    label mixes latin and non-latin scripts (classic lookalike pattern).
    Pure single-script IDNs (e.g. legitimate CJK/Arabic domains) return False.
    """
    if not domain:
        return False
    # Pure ASCII: cannot be a unicode homograph attack.
    if all(ord(c) < 128 for c in domain):
        return False
    for label in domain.lower().split("."):
        has_latin = any("a" <= c <= "z" for c in label)
        has_non_latin = any(ord(c) > 127 for c in label)
        if has_latin and has_non_latin:
            return True
        # All-non-latin label that IDNA-encodes to punycode alongside
        # ASCII labels in the same domain is also suspicious (mixed labels).
        if has_non_latin and not has_latin:
            try:
                label.encode("idna")
                return True
            except Exception:
                return True
    return False


def _extract_hostname(normalized: str) -> tuple[str, str]:
    """Return (raw_unicode_host, normalized_ascii_host) without userinfo/port."""
    parsed = urlparse(normalized)
    raw = (parsed.hostname or "").lower().strip().rstrip(".")
    if not raw:
        # Fallback for malformed URLs: strip scheme manually.
        raw = re.sub(r"^https?://", "", normalized, flags=re.IGNORECASE).split("/")[0]
        raw = raw.split("@")[-1].split(":")[0].lower().strip().rstrip(".")
    try:
        ascii_host = raw.encode("idna").decode("ascii")
    except Exception:
        ascii_host = raw
    return raw, ascii_host


def analyze_urls(text: str) -> dict:
    raw_urls = re.findall(r"https?://[^\s)<>\]]+|www\.[^\s)<>\]]+", text or "", flags=re.IGNORECASE)
    # Strip trailing punctuation captured by the regex (.,;:!?'" etc).
    urls = [u.rstrip(".,;:!?'\"") for u in raw_urls if u.strip(".,;:!?'\"")]
    findings = []
    details = []

    for url in urls:
        normalized = url if re.match(r"^https?://", url, re.IGNORECASE) else f"http://{url}"
        raw_domain, domain = _extract_hostname(normalized)

        if domain.startswith("www."):
            domain = domain[4:]

        tld = domain.rsplit('.', 1)[-1] if '.' in domain else ""
        url_findings = []

        if tld in SUSPICIOUS_TLDS:
            url_findings.append(f"Suspicious TLD (.{tld}) in {url}")
            details.append(f"Suspicious TLD (.{tld}) in {url}")

        if re.search(r"\d{4,}", domain.replace(".", "")):
            url_findings.append(f"Domain with excessive digits: {domain}")
            details.append(f"Domain with excessive digits: {domain}")

        if is_homograph(raw_domain):
            url_findings.append(f"Homograph attack detected in domain: {raw_domain}")
            details.append(f"Homograph attack detected in domain: {raw_domain}")

        if PHISHING_PATTERNS.search(domain):
            url_findings.append(f"Phishing-related keywords in domain: {domain}")
            details.append(f"Phishing-related keywords in domain: {domain}")

        if domain in URL_SHORTENERS:
            url_findings.append(f"URL shortener detected: {domain}")
            details.append(f"URL shortener detected: {domain}")

        if re.match(r"^\d+\.\d+\.\d+\.\d+$", domain):
            url_findings.append(f"IP-based URL (bypasses domain filtering): {url}")
            details.append(f"IP-based URL (bypasses domain filtering): {url}")

        if domain.count(".") >= 3:
            url_findings.append(f"Excessive subdomains in {domain}")
            details.append(f"Excessive subdomains in {domain}")

        findings.append({"url": url, "domain": domain, "findings": url_findings})

    suspicious_urls = sorted({f["url"] for f in findings if f["findings"]})

    return {
        "urls": urls,
        "count": len(urls),
        # Unique suspicious URLs — one entry per URL, never one per rule hit.
        "suspicious_urls": suspicious_urls,
        "suspicious_count": len(suspicious_urls),
        "details": sorted(set(details)),
        # Per-URL evidence: one record per URL with its list of findings.
        "url_findings": findings,
    }
