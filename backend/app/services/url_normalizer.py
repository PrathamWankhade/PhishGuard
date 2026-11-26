"""URL normalization for lexical analysis and safe fetching.

Shared by `url_analyzer.py` (passive) and `url_safety.py` (opt-in live) so both
see the same canonical form of a URL. Divergent normalization between the two
is how a URL ends up analyzed as one host and fetched as another.
"""
import re
from urllib.parse import urlsplit

DEFAULT_PORTS = {"http": 80, "https": 443}


def normalize_scheme(url: str) -> str:
    """Lowercase the scheme and reject anything that is not http/https."""
    return urlsplit(url.strip()).scheme.lower() if url.strip() else ""


def hostname_of(url: str) -> str:
    """Return the lowercased hostname with no userinfo, port, or trailing dot.

    Uses the parsed hostname rather than a string split so `\@`-style userinfo
    confusion cannot put an internal host in the analyst's view.
    """
    try:
        parts = urlsplit(url.strip())
        host = parts.hostname
    except ValueError:
        host = None
    if host:
        return host.rstrip(".").lower()
    # Fallback for scheme-less or malformed input.
    stripped = re.sub(r"^https?://", "", url.strip(), flags=re.IGNORECASE)
    return stripped.split("/")[0].split("@")[-1].split(":")[0].rstrip(".").lower()


def strip_default_port(url: str) -> str:
    """Remove an explicit port that equals the scheme's default.

    `https://example.com:443/x` and `https://example.com/x` are the same host;
    keeping both forms would double-count in any per-host aggregation.
    """
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url
    if not parts.port or parts.scheme.lower() not in DEFAULT_PORTS:
        return url.strip()
    if parts.port != DEFAULT_PORTS[parts.scheme.lower()]:
        return url.strip()
    netloc = parts.hostname or ""
    if parts.username:
        netloc = f"{parts.username}@{netloc}"
    return parts._replace(netloc=netloc).geturl()


def punycode_host(hostname: str) -> str:
    """Return the ASCII (punycode) form of a hostname, for grouping.

    `münchen.de` and `xn--mnchen-3ya.de` are the same registrable host; an
    analysis that treats them separately can be evaded by mixing forms.
    Undecodable input is returned unchanged — a host that will not encode is
    already suspicious, and `url_analyzer.is_homograph` reports it as such.
    """
    if not hostname:
        return hostname
    try:
        return hostname.encode("idna").decode("ascii")
    except Exception:
        return hostname


def normalize_all(url: str) -> dict:
    """Full normalization record for one URL.

    Returns the components every consumer needs, so no caller has to re-derive
    the host or port and risk disagreeing with another caller. Scheme-less
    input (`www.example.com/a`) has no parsed hostname, so it falls back to the
    same textual extraction `hostname_of()` uses — the two must agree.
    """
    raw = (url or "").strip()
    try:
        parts = urlsplit(raw)
        host = parts.hostname
        port = parts.port
    except ValueError:
        parts, host, port = None, None, None
    host = (host or "").rstrip(".").lower()
    scheme = (parts.scheme.lower() if parts else "") if raw else ""
    if not host and raw:
        host = hostname_of(raw)
    if port is None and scheme in DEFAULT_PORTS:
        port = DEFAULT_PORTS[scheme]
    return {
        "url": strip_default_port(raw),
        "scheme": scheme,
        "host": host,
        "port": port,
        "host_punycode": punycode_host(host),
        "path": (parts.path if parts else "") or "",
        "query": (parts.query if parts else "") or "",
    }