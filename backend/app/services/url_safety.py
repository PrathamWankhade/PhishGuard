"""SSRF-safe outbound URL fetching.

Used only by operators who explicitly enable live URL analysis
(`URL_REPUTATION_ENABLED=true`). The default path is passive lexical analysis
(`url_analyzer.py`), which never opens a connection.

Why this module exists: fetching a URL supplied by an attacker is a request to
an attacker-chosen host and port. Without the guards below, a single scanned
email can be used to reach the service's own loopback interface, the cloud
metadata endpoint (169.254.169.254), an internal database, or the container
runtime's socket. A "URL reputation" feature is therefore a security feature
first.

Guards, in the order they are applied:

  1. Scheme allow-list — http/https only. No file:, ftp:, gopher:, data:.
  2. No credentials in the URL — userinfo is rejected outright, so a
     `https://user:pass@host/` cannot be used to exfiltrate or confuse auth.
  3. Port allow-list — 80/443 only (plus the scheme's default).
  4. Parse before connect — the host is extracted from the parsed URL, not
     from a string slice, so `https://evil.com\@169.254.169.254/` style
     confusion does not pick an internal host.
  5. Resolve and validate EVERY address — the hostname is resolved and every
     returned A/AAAA record must be public. One private record rejects the
     fetch, not "the first bad one".
  6. Connect to the validated IP, not the name — the connection is pinned to
     the IP that passed validation, which closes the DNS-rebinding window
     between the check and the connect.
  7. Revalidate on every redirect — a 302 to an internal address is checked
     again from step 1, with the same guards.
  8. Response size cap — the stream is read in bounded chunks and truncated,
     so a hostile endpoint cannot stream unbounded data into memory.
  9. Strict timeouts — connect and read, both.
  10. No redirects to non-allow-listed schemes, and a hard redirect ceiling.

Nothing here is a substitute for egress filtering at the network layer; it is
defence in depth for the case where the service can reach internal space.
"""
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_PORTS = {80, 443}
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 512 * 1024
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 10.0


class UnsafeURLError(Exception):
    """Raised when a URL fails a safety guard. Callers must treat this as a
    hard refusal, never as "fetch empty and continue"."""


@dataclass(frozen=True)
class SafeURL:
    url: str
    host: str
    port: int
    scheme: str
    ip: str


# Carrier-grade NAT space (100.64.0.0/10). Not universally flagged as private
# by the stdlib, and it is not globally routable, so it must not be treated as
# a public target.
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")
_CGNAT_V4 = {ipaddress.ip_address("100.64.0.0"), ipaddress.ip_address("100.127.255.255")}


def _is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    # IPv4-mapped IPv6 (::ffff:127.0.0.1) peers at the IPv4 form, so the
    # checks below must run on the unwrapped address.
    inner = ip.ipv4_mapped if getattr(ip, "ipv4_mapped", None) is not None else ip
    if inner in _CGNAT_V4 or (
        inner.version == 4 and inner in _SHARED_ADDRESS_SPACE
    ):
        return False
    return not (
        inner.is_private
        or inner.is_loopback
        or inner.is_link_local
        or inner.is_reserved
        or inner.is_multicast
        or inner.is_unspecified
        # 6to4/Teredo tunnels can otherwise smuggle an internal IPv4 target
        # past an IPv4-only check.
        or getattr(inner, "ipv4_mapped", None) is not None
        or getattr(inner, "sixtofour", None) is not None
        or getattr(inner, "teredo", None) is not None
    )


def resolve_public_ips(host: str, port: int) -> list[str]:
    """Resolve host and return only its public addresses.

    Raises UnsafeURLError if any resolved address fails the public-IP check —
    one private record rejects the whole name, so a dual-homed host cannot
    pass by listing a public address first.
    """
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"DNS resolution failed for {host}: {exc}") from exc

    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise UnsafeURLError(f"No addresses resolved for {host}")

    bad = sorted(a for a in addresses if not _is_public_ip(a))
    if bad:
        raise UnsafeURLError(f"{host} resolves to non-public address(es): {', '.join(bad)}")

    return sorted(addresses)


def validate_url(url: str) -> SafeURL:
    """Parse and validate a URL for outbound fetching. Raises UnsafeURLError."""
    if not url or not url.strip():
        raise UnsafeURLError("empty URL")

    try:
        parts = urlsplit(url.strip())
    except ValueError as exc:
        raise UnsafeURLError(f"unparseable URL: {exc}") from exc

    scheme = (parts.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"scheme {scheme!r} is not allowed ({', '.join(ALLOWED_SCHEMES)})")

    # Userinfo is rejected outright: credentials in the URL are both an
    # SSRF-confusion vector and a way to smuggle headers.
    if parts.username or parts.password:
        raise UnsafeURLError("URLs with embedded credentials are not allowed")

    try:
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise UnsafeURLError(f"invalid host/port: {exc}") from exc

    if not host:
        raise UnsafeURLError("URL has no host")
    host = host.rstrip(".")

    if port is None:
        port = 443 if scheme == "https" else 80
    if port not in ALLOWED_PORTS:
        raise UnsafeURLError(f"port {port} is not allowed (80, 443 only)")

    public_ips = resolve_public_ips(host, port)

    return SafeURL(
        url=url.strip(),
        host=host,
        port=port,
        scheme=scheme,
        ip=public_ips[0],
    )


def check_fetch_allowed() -> bool:
    """Live URL fetching is opt-in. Passive lexical analysis is the default."""
    import os

    return os.environ.get("URL_REPUTATION_ENABLED", "").lower() in ("1", "true", "yes")


def fetch_safely(url: str, *, max_bytes: int = MAX_RESPONSE_BYTES):
    """Fetch a URL with all guards applied, including on redirects.

    Returns (final_url, body_bytes). Raises UnsafeURLError for any violation.
    Deliberately does not forward cookies, auth headers, or credentials.
    """
    import http.client

    if not check_fetch_allowed():
        raise UnsafeURLError(
            "live URL fetching is disabled (URL_REPUTATION_ENABLED unset); "
            "passive lexical analysis is the default"
        )

    current = url
    for _ in range(MAX_REDIRECTS + 1):
        safe = validate_url(current)

        conn_class = (
            http.client.HTTPSConnection if safe.scheme == "https" else http.client.HTTPConnection
        )
        conn = conn_class(safe.ip, safe.port, timeout=CONNECT_TIMEOUT)
        try:
            # The Host header carries the original name; the TCP connection is
            # pinned to the validated IP (DNS-rebinding guard).
            path = _request_path(current, safe)
            conn.request("GET", path, headers={"Host": safe.host, "Connection": "close"})
            response = conn.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise UnsafeURLError("redirect without Location")
                current = _resolve_relative(current, location)
                continue
            body = _read_bounded(response, max_bytes)
            return current, body
        finally:
            conn.close()

    raise UnsafeURLError(f"exceeded {MAX_REDIRECTS} redirects")


def _request_path(url: str, safe: SafeURL) -> str:
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"
    return path


def _resolve_relative(base: str, location: str) -> str:
    from urllib.parse import urljoin

    return urljoin(base, location)


def _read_bounded(response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(8192)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UnsafeURLError(f"response exceeded {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)