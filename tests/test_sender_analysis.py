import pytest

from backend.app.services.sender_analyzer import analyze_sender


def test_suspicious_tld():
    result = analyze_sender("admin@bank-secure.xyz")
    assert result["risk"] > 0
    assert len(result["reasons"]) > 0


def test_impersonation_domain():
    result = analyze_sender("support@paypal-secure-login.com")
    assert result["risk"] > 0
    assert any("impersonation" in r.lower() for r in result["reasons"])


def test_trusted_domain():
    result = analyze_sender("john@gmail.com")
    assert result["risk"] == 0


def test_excessive_subdomains():
    result = analyze_sender("alert@security.alert.bank.verify.com")
    assert result["risk"] > 0


def test_empty_sender():
    result = analyze_sender("")
    assert result["risk"] == 0


def test_none_sender():
    result = analyze_sender(None)
    assert result["risk"] == 0


# --- Regression guard: legitimate subdomains of trusted brands -------------
#
# The lookalike check used to be `domain.endswith("." + trusted)`, which can
# only be true for a REAL subdomain of the brand -- so ordinary enterprise
# mail (app.asana.com, mail.google.com, accounts.google.com) was scored as
# "possible domain impersonation" and inflated the sender channel of the risk
# score. That is a false-positive class on normal traffic, not a detection.

@pytest.mark.parametrize("sender", [
    "admin@mail.google.com",
    "no-reply@accounts.google.com",
    "admin@app.asana.com",
    "team@notion.so",
    "user@zoom.us",
])
def test_trusted_brand_subdomains_are_not_impersonation(sender):
    result = analyze_sender(sender)
    assert result["risk"] == 0, f"{sender} should not be penalised: {result['reasons']}"
    assert result["reasons"] == []


def test_brand_name_as_label_is_flagged():
    # A brand word used as a whole label OUTSIDE the brand's own hierarchy is
    # the actual impersonation pattern.
    result = analyze_sender("support@google-secure.com")
    assert result["risk"] > 0
    assert any("brand name" in r.lower() for r in result["reasons"])


def test_brand_substring_is_not_a_brand_label():
    # "apple" is a substring of "applesauce" but not a label of it -- matching
    # on substrings would flag unrelated legitimate domains.
    result = analyze_sender("someone@applesauce.com")
    assert result["risk"] == 0, result["reasons"]


def test_risk_is_capped_at_30():
    result = analyze_sender("admin@secure-login.bank.verify.com")
    assert result["risk"] <= 30
