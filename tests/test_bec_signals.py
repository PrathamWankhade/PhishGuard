"""Business-email-compromise / fraud signals.

BEC findings are keyword evidence, never a verdict: they contribute capped
points into the decision engine. These tests pin the signal vocabulary and,
importantly, the false-positive cases a keyword matcher produces — so a future
"tightening" of a pattern is a deliberate, reviewed change rather than a silent
behaviour shift.
"""
from backend.app.services.bec_analyzer import analyze_bec


def test_financial_fraud_pattern():
    r = analyze_bec("Please complete the wire transfer today.")
    assert r["risk"] > 0
    assert any("financial" in x.lower() for x in r["reasons"])


def test_secrecy_pressure_pattern():
    r = analyze_bec("Handle this discreetly and do not tell anyone else.")
    assert r["risk"] > 0
    assert any("secrecy" in x.lower() for x in r["reasons"])


def test_executive_impersonation_language():
    r = analyze_bec("I am the CEO and I need this handled now.")
    assert r["risk"] > 0
    assert any("executive" in x.lower() for x in r["reasons"])


def test_credential_harvest_pattern():
    r = analyze_bec("Verify your password to prevent account suspension.")
    assert r["risk"] > 0
    assert any("credential" in x.lower() for x in r["reasons"])


def test_benign_email_is_quiet():
    r = analyze_bec("Reminder: the quarterly report is attached for review.")
    assert r["reasons"] == []
    assert r["risk"] == 0


def test_empty_text_is_quiet():
    r = analyze_bec("")
    assert r["reasons"] == []
    assert r["risk"] == 0


def test_risk_is_capped():
    r = analyze_bec(
        "I am the CEO. Keep this confidential, do not tell the board, "
        "and wire the transfer to the new routing number, then verify your password."
    )
    assert r["risk"] <= 15


# --- Known false positives, pinned so changes are deliberate ----------------
#
# Keyword matching cannot distinguish a fraud request from ordinary corporate
# language. The decision engine absorbs this by capping these points (and by
# requiring other evidence before a Phishing verdict), but the FP surface is
# documented rather than hidden.

def test_executive_title_alone_flags_ordinary_corporate_mail():
    # "board" appears in routine internal email. This is expected behaviour of
    # a keyword channel, not a bug — the cap and the evidence requirement stop
    # it reaching a verdict on its own.
    r = analyze_bec("Please review the board deck before Thursday.")
    assert any("executive" in x.lower() for x in r["reasons"])