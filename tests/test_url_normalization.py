"""URL normalization shared by the passive analyzer and the live fetcher.

If these two paths normalize a URL differently, the URL is analyzed as one host
and fetched as another. These tests pin the shared form both use.
"""
from backend.app.services.url_normalizer import (
    hostname_of,
    normalize_all,
    normalize_scheme,
    punycode_host,
    strip_default_port,
)


def test_hostname_strips_userinfo():
    assert hostname_of("https://user:pass@Example.com/x") == "example.com"


def test_hostname_strips_port_and_trailing_dot():
    assert hostname_of("https://Example.com:8080/path") == "example.com"
    assert hostname_of("https://example.com./path") == "example.com"


def test_hostname_lowercases():
    assert hostname_of("HTTPS://EXAMPLE.COM/A") == "example.com"


def test_hostname_of_scheme_less_input():
    assert hostname_of("www.example.com/a/b") == "www.example.com"


def test_userinfo_confusion_cannot_pick_an_internal_host():
    # The parsed hostname must be the attacker-controlled name, not the
    # internal address after the backslash.
    assert hostname_of("https://169.254.169.254\\@example.com/") == "example.com"


def test_scheme_default_port_is_stripped():
    assert strip_default_port("https://example.com:443/x") == "https://example.com/x"
    assert strip_default_port("http://example.com:80/x") == "http://example.com/x"


def test_explicit_non_default_port_is_kept():
    assert ":8080" in strip_default_port("http://example.com:8080/x")
    assert ":8443" in strip_default_port("https://example.com:8443/x")


def test_scheme_is_lowercased():
    assert normalize_scheme("HTTPS://example.com/") == "https"
    assert normalize_scheme("http://example.com/") == "http"


def test_scheme_less_url_has_no_scheme():
    assert normalize_scheme("example.com/path") == ""


def test_punycode_host_groups_idn_forms():
    # The same registrable host in two notations must normalize identically,
    # or per-host aggregation can be evaded by mixing forms.
    unicode_form = punycode_host("münchen.de")
    ascii_form = punycode_host("xn--mnchen-3ya.de")
    assert unicode_form == ascii_form == "xn--mnchen-3ya.de"


def test_punycode_host_leaves_ascii_unchanged():
    assert punycode_host("example.com") == "example.com"


def test_punycode_host_is_idempotent():
    once = punycode_host("münchen.de")
    assert punycode_host(once) == once


def test_undecodable_host_returned_unchanged():
    # A host that will not encode is already suspicious; the analyzer reports
    # it as a homograph rather than silently dropping the URL.
    assert punycode_host("xn--invalid..label") == "xn--invalid..label"


def test_normalize_all_reports_every_component():
    record = normalize_all("https://User:Pass@Example.com:443/a?b=c")
    assert record["host"] == "example.com"
    assert record["port"] == 443
    assert record["scheme"] == "https"
    assert record["host_punycode"] == "example.com"
    assert record["path"] == "/a"
    assert record["query"] == "b=c"
    assert ":443" not in record["url"]


def test_normalize_all_handles_scheme_less_input():
    record = normalize_all("www.example.com/a")
    assert record["host"] == "www.example.com"
    assert record["port"] is None
    assert record["scheme"] == ""