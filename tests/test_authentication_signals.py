"""Header-authentication and reply-path signals.

The behaviour under test is mostly the TRUST BOUNDARY: authentication results
that arrive with the email are caller-supplied and forgeable, so they must be
weak, explicitly labelled signals — never treated as server-verified proof.
"""
from backend.app.services.auth_analyzer import analyze_auth


def test_reply_to_domain_mismatch_is_flagged():
    r = analyze_auth(sender="billing@company.com", reply_to="billing@company-support.xyz")
    assert r["risk"] > 0
    assert any("reply-to" in x.lower() for x in r["reasons"])


def test_return_path_domain_mismatch_is_flagged():
    r = analyze_auth(sender="billing@company.com", return_path="bounce@mailer.xyz")
    assert r["risk"] > 0
    assert any("return-path" in x.lower() for x in r["reasons"])


def test_matching_reply_to_is_not_flagged():
    r = analyze_auth(sender="billing@company.com", reply_to="billing@company.com")
    assert r["reasons"] == []
    assert r["risk"] == 0


def test_no_evidence_stays_quiet():
    # Missing auth evidence is unknown, not malicious.
    r = analyze_auth(sender="a@company.com", reply_to="", return_path="", auth_results="")
    assert r["reasons"] == []
    assert r["risk"] == 0


def test_untrusted_auth_failure_is_weak_and_labelled():
    r = analyze_auth(auth_results="spf=fail (sender not authorised)")
    assert r["risk"] > 0
    reason = next(x for x in r["reasons"] if "spf" in x)
    assert "caller-supplied" in reason.lower(), "a forged failure must not read as verified"


def test_trusted_auth_failure_is_stronger_than_untrusted():
    untrusted = analyze_auth(auth_results="spf=fail dkim=fail dmarc=fail")
    trusted = analyze_auth(auth_results="spf=fail dkim=fail dmarc=fail", trusted=True)
    assert trusted["risk"] > untrusted["risk"]
    assert all("caller-supplied" in x.lower() for x in untrusted["reasons"] if "spf" in x)
    assert not any("caller-supplied" in x.lower() for x in trusted["reasons"])


def test_untrusted_pass_is_informational_only():
    # A pass pasted into the request body proves nothing, and must not earn
    # risk points (or negative ones).
    r = analyze_auth(auth_results="spf=pass dkim=pass dmarc=pass")
    assert r["risk"] == 0
    assert any("unverified" in x.lower() for x in r["reasons"])


def test_trusted_pass_is_marked_verified():
    r = analyze_auth(auth_results="spf=pass", trusted=True)
    assert r["risk"] == 0
    assert any("verified" in x.lower() for x in r["reasons"])


def test_malformed_auth_string_is_ignored():
    r = analyze_auth(auth_results="totally not an authentication-results header")
    assert r["reasons"] == []
    assert r["risk"] == 0


def test_partial_auth_header_parses_independently():
    r = analyze_auth(auth_results="dkim=pass spf=fail")
    assert any("dkim" in x.lower() for x in r["reasons"])
    assert any("spf" in x.lower() for x in r["reasons"])


def test_risk_is_capped():
    r = analyze_auth(
        sender="a@company.com",
        reply_to="a@other.com",
        return_path="b@other.com",
        auth_results="spf=fail dkim=fail dmarc=fail",
        trusted=True,
    )
    assert r["risk"] <= 20