"""SSRF guards for outbound URL fetching.

These are the tests that decide whether live URL analysis can be enabled at
all. Each one corresponds to a way an attacker-controlled URL could otherwise
reach the service's own network, the cloud metadata endpoint, or an internal
dependency. Network calls are never made: the resolver and connection are
patched.
"""
from unittest.mock import patch

import io
from unittest.mock import patch

import pytest

from backend.app.services.url_safety import (
    ALLOWED_SCHEMES,
    UnsafeURLError,
    _is_public_ip,
    check_fetch_allowed,
    fetch_safely,
    resolve_public_ips,
    validate_url,
)


# --- fixtures: no real network in these tests -------------------------------

PUBLIC_IPS = [("example.com", 443, 0, ("93.184.216.34", 443))]


@pytest.fixture
def _fake_public_dns():
    """Every hostname resolves to a public address."""
    import socket as _socket

    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [(_socket.AF_INET, _socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 443))]

    with patch("socket.getaddrinfo", side_effect=fake_getaddrinfo):
        yield


@pytest.fixture
def _fake_public_dns_mixed():
    """A dual-homed host: one public record plus one private."""
    import socket as _socket

    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [
            (_socket.AF_INET, _socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 443)),
            (_socket.AF_INET, _socket.SOCK_STREAM, 6, "", ("127.0.0.1", port or 80)),
        ]

    with patch("socket.getaddrinfo", side_effect=fake_getaddrinfo):
        yield


class _FakeResponse:
    def __init__(self, status=200, headers=None, body=b""):
        self.status = status
        self._headers = headers or {}
        self._body = io.BytesIO(body)

    def getheader(self, name, default=None):
        return self._headers.get(name, default)

    def read(self, n=-1):
        return self._body.read(n)


class _FakeConnection:
    """Records requests, returns a scripted response. No socket is opened."""

    def __init__(self, response=None):
        self.response = response or _FakeResponse()
        self.requests = []

    def request(self, method, path, headers=None):
        self.requests.append((method, path, headers))

    def getresponse(self):
        return self.response

    def close(self):
        pass


@pytest.fixture
def _oversized_response(monkeypatch):
    monkeypatch.setenv("URL_REPUTATION_ENABLED", "true")
    response = _FakeResponse(body=b"x" * (600 * 1024))
    conn = _FakeConnection(response=response)
    with (
        patch("backend.app.services.url_safety.validate_url",
              return_value=type("S", (), {"url": "https://example.com/big", "host": "example.com",
                                          "port": 443, "scheme": "https", "ip": "93.184.216.34"})()),
        patch("http.client.HTTPSConnection", return_value=conn),
    ):
        yield conn


@pytest.fixture
def _redirect_loop(monkeypatch):
    monkeypatch.setenv("URL_REPUTATION_ENABLED", "true")
    response = _FakeResponse(status=302, headers={"Location": "https://example.com/loop"})
    conn = _FakeConnection(response=response)
    with (
        patch("backend.app.services.url_safety.validate_url",
              return_value=type("S", (), {"url": "https://example.com/loop", "host": "example.com",
                                          "port": 443, "scheme": "https", "ip": "93.184.216.34"})()),
        patch("http.client.HTTPSConnection", return_value=conn),
    ):
        yield conn


@pytest.fixture
def _redirect_to_metadata(monkeypatch):
    monkeypatch.setenv("URL_REPUTATION_ENABLED", "true")
    response = _FakeResponse(status=302,
                             headers={"Location": "http://169.254.169.254/latest/meta-data/"})
    conn = _FakeConnection(response=response)
    safe = type("S", (), {"url": "https://example.com/redirect", "host": "example.com",
                          "port": 443, "scheme": "https", "ip": "93.184.216.34"})()

    def _validate(url):
        if "169.254" in url:
            raise UnsafeURLError("169.254.169.254 resolves to non-public address 169.254.169.254")
        return safe

    with (
        patch("backend.app.services.url_safety.validate_url", side_effect=_validate),
        patch("http.client.HTTPSConnection", return_value=conn),
    ):
        yield conn


# --- scheme allow-list ------------------------------------------------------

@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "ftp://internal.host/secrets",
    "gopher://127.0.0.1:6379/_INFO",
    "data:text/html,hello",
    "dict://127.0.0.1:11211/stat",
    "jar:http://evil.com!/",
    "//example.com/path",
    "example.com/path",
])
def test_non_http_schemes_are_rejected(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


def test_http_and_https_are_allowed():
    assert set(ALLOWED_SCHEMES) == {"http", "https"}


# --- credentials ------------------------------------------------------------

def test_userinfo_is_rejected():
    with pytest.raises(UnsafeURLError, match="credentials"):
        validate_url("https://user:pass@example.com/")


def test_userinfo_obfuscation_is_rejected():
    # A bare username is still userinfo, and still rejected.
    with pytest.raises(UnsafeURLError, match="credentials"):
        validate_url("https://user@example.com/")


# --- port allow-list --------------------------------------------------------

@pytest.mark.parametrize("port", [22, 6379, 5432, 11211, 9200, 8080, 25, 2375])
def test_non_web_ports_are_rejected(port):
    with pytest.raises(UnsafeURLError, match="port"):
        validate_url(f"https://example.com:{port}/")


@pytest.mark.parametrize("url", [
    "http://example.com/", "http://example.com:80/",
    "https://example.com/", "https://example.com:443/",
])
def test_web_ports_allowed_with_public_host(url, _fake_public_dns):
    safe = validate_url(url)
    assert safe.host == "example.com"
    assert safe.port in (80, 443)


# --- private / internal IP targets -----------------------------------------

@pytest.mark.parametrize("host", [
    "127.0.0.1", "localhost", "0.0.0.0", "10.0.0.5", "192.168.1.1",
    "172.16.0.1", "169.254.169.254",   # cloud metadata
    "[::1]", "169.254.0.1", "100.64.0.1",
    "metadata.google.internal", "instance-data",
])
def test_internal_targets_are_rejected(host):
    with pytest.raises(UnsafeURLError):
        validate_url(f"https://{host}/")

def test_metadata_endpoint_is_rejected():
    with pytest.raises(UnsafeURLError):
        validate_url("http://169.254.169.254/latest/meta-data/")


def test_single_private_record_rejects_dual_homed_host(_fake_public_dns_mixed):
    """One private address among several must reject the whole fetch — a host
    that lists a public address first cannot pass."""
    with pytest.raises(UnsafeURLError, match="non-public"):
        resolve_public_ips("dual-homed.example.com", 443)


def test_public_resolution_succeeds(_fake_public_dns):
    ips = resolve_public_ips("example.com", 443)
    assert ips and all(_is_public_ip(ip) for ip in ips)


# --- tunneled / mapped IPv6 ------------------------------------------------

@pytest.mark.parametrize("ip", [
    "::ffff:127.0.0.1",     # IPv4-mapped loopback
    "::ffff:169.254.169.254",
    "2002:7f00:1::",        # 6to4 for 127.0.0.1
])
def test_tunneled_ipv6_is_not_public(ip):
    assert _is_public_ip(ip) is False


@pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1", "93.184.216.34"])
def test_ordinary_public_ips_are_public(ip):
    assert _is_public_ip(ip) is True


# --- hostname parsing ------------------------------------------------------

def test_backslash_userinfo_cannot_select_internal_host():
    # `evil.com\@internal` style confusion must not make the host internal.
    with pytest.raises(UnsafeURLError):
        validate_url("https://169.254.169.254\\@example.com/")


def test_empty_and_blank_urls_rejected():
    for url in ("", "   ", None):
        with pytest.raises(UnsafeURLError):
            validate_url(url)


# --- opt-in gate -----------------------------------------------------------

def test_live_fetch_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("URL_REPUTATION_ENABLED", raising=False)
    assert check_fetch_allowed() is False


def test_live_fetch_can_be_enabled(monkeypatch):
    monkeypatch.setenv("URL_REPUTATION_ENABLED", "true")
    assert check_fetch_allowed() is True


def test_fetch_refuses_when_disabled(monkeypatch):
    monkeypatch.delenv("URL_REPUTATION_ENABLED", raising=False)
    with pytest.raises(UnsafeURLError, match="disabled"):
        fetch_safely("https://example.com/")


# --- response bound --------------------------------------------------------

def test_large_response_is_truncated(_oversized_response):
    with pytest.raises(UnsafeURLError, match="exceeded"):
        _, body = fetch_safely("https://example.com/big")
        _ = body


# --- redirect ceiling ------------------------------------------------------

def test_redirect_ceiling(_redirect_loop):
    with pytest.raises(UnsafeURLError, match="redirect"):
        fetch_safely("https://example.com/loop")


def test_redirect_to_internal_is_revalidated(_redirect_to_metadata):
    """A 302 to an internal address is checked again from step 1."""
    with pytest.raises(UnsafeURLError, match="non-public|port|scheme|resolves"):
        fetch_safely("https://example.com/redirect")