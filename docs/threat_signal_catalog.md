# Threat signal catalog

Every deterministic rule the decision engine can fire on, what evidence it
produces, how many risk points it contributes, and where it is wrong.

The engine deliberately separates **what the model says** from **what the rules
say**: the model contributes `phishing_probability * 100` and the analyzers
below add capped points on top. No rule can reach a verdict alone.

```
risk = min(99, round(P(phishing)*100 + url_risk + sender_risk + evidence_risk, 2))
```

| Channel | Source | Points | Effective cap |
|---|---|---|---|
| Model | TF-IDF + soft-voting ensemble | `P(phishing) * 100` | 100 (then capped by formula) |
| URL | `services/url_analyzer.py` | 4 per **unique** suspicious URL | 20 |
| Sender | `services/sender_analyzer.py` | see rules | 30 |
| Evidence | `auth_analyzer.py` + `bec_analyzer.py` | see rules | 10 (applied by `phishing_detector`) |

> Note: `auth_analyzer` caps itself at 20 and `bec_analyzer` at 15, but the
> *effective* cap for both combined is 10, applied by the detector. The
> per-analyzer numbers are local maxima, not what they contribute in practice.

Verdict thresholds: risk ≥ 75 → `Phishing Email`, ≥ 45 → `Suspicious Email`,
else `Safe Email`.

---

## URL analyzer (`services/url_analyzer.py`)

Passive and lexical **by default** — no reputation lookup, no redirect
following. An opt-in live mode exists (`URL_REPUTATION_ENABLED=true`) that
fetches through `services/url_safety.py` with SSRF guards; it is off unless an
operator enables it. See [security.md](security.md).

| Signal | Detection | Points |
|---|---|---|
| Suspicious TLD | TLD in a curated set (`xyz`, `top`, `click`, `zip`, `ru`, `cn`, `tk`, `ml`, `ga`, `cf`, …) | counts toward 4/URL |
| Excessive digits | 4+ consecutive digits in the domain, dots removed | counts toward 4/URL |
| Homograph / mixed script | A label mixing Latin with another script (Cyrillic lookalikes), or two non-Latin scripts in one label; `xn--` labels are IDNA-decoded before analysis | counts toward 4/URL |
| Phishing keywords in domain | `credential`, `authenticate`, `reset-password`, `secure-login`, `banking-verify` | counts toward 4/URL |
| URL shortener | Domain in a shortener set (`bit.ly`, `tinyurl.com`, `t.co`, …) | counts toward 4/URL |
| IP-based host | Domain is an IPv4 literal | counts toward 4/URL |
| Excessive subdomains | 3+ dots in the host | counts toward 4/URL |

Points are counted **per unique suspicious URL**, not per rule hit, so a URL
tripping five rules contributes 4 once — the rule set is evidence, the count is
the signal. Per-URL evidence stays visible via `url_findings`.

**Known false positives.** Entire `.ru`/`.cn` registrant populations; a
legitimate newsletter using `bit.ly`; CDN and SaaS hosts with deep subdomain
paths (`a.b.c.cloudfront.net`); hyphenated company names that look like
`secure-login`. A suspicious URL alone contributes at most 20 points, so it
cannot produce a `Phishing Email` verdict by itself.

**Not implemented.** Reputation/age lookup, redirect-chain expansion, and page
content — all require outbound fetching with SSRF guards first.

---

## Sender analyzer (`services/sender_analyzer.py`)

| Signal | Detection | Points |
|---|---|---|
| Suspicious TLD | Same TLD set as the URL analyzer | 10 |
| Impersonation keywords in domain | A keyword from the list (`security-alert`, `verify`, `login`, `support-`, `help-desk`, `no-reply`, `account`, `secure`, `banking`, …) appears in the domain, **unless** the domain is inside a trusted brand | 10 |
| Brand name used outside its own domain | A trusted brand name appears as a **whole label** of a domain that is not inside that brand's hierarchy (`google-secure.com`, `paypal-login.xyz`) | 8 |
| Suspicious sender pattern | Local part imitates a role address (`admin`, `support`, `noreply`, …) **and** the TLD is suspicious | 5 |
| Excessive subdomains | 3+ dots in the sender domain | 5 |

**Trusted-brand suppression.** A domain equal to, or a subdomain of, a curated
trusted base (`app.asana.com`, `mail.google.com`, `accounts.google.com`) never
triggers the impersonation-keyword or brand rules. Only the brand's own
registrars can create anything under it, so those hosts are not attacker
lookalikes. This is a false-positive fix, and `tests/test_sender_analysis.py`
pins it: before the fix, ordinary enterprise subdomains were reported as
"possible domain impersonation".

**Known false positives.** Brand-name labelling flags legitimate
`<brand>-related` businesses outside the list's brands (`notion-studio.com`).
Matching is on whole labels, so incidental substrings are safe
(`applesauce.com` does not match `apple`).

**Not implemented.** Display-name spoofing (the analyzer sees only the
address, not `From: "PayPal Security" <x@y>`), Unicode/IDN display-name
analysis, and free-mail-vs-corporate policy — these need the caller to supply
and the parser to expose the structured header.

---

## Authentication analyzer (`services/auth_analyzer.py`)

The important rule here is the **trust boundary**.

| Signal | Detection | Points |
|---|---|---|
| Reply-To domain differs from sender | `_domain_of(reply_to) != _domain_of(sender)` | 8 |
| Return-Path domain differs from sender | same comparison on the envelope sender | 5 |
| Auth failure, **trusted** infrastructure | `spf/dkim/dmarc = fail\|softfail\|permerror`, `trusted=True` | 8 each |
| Auth failure, **untrusted** (public API, uploads) | same verdict, `trusted=False` | 4 each, labelled `(caller-supplied, not server-verified)` |
| Auth pass | reported as a reason only | **0** |

Authentication results that arrive with the email are caller-supplied and can
be forged: a pasted `spf=pass` proves nothing. Only results added by receiving
infrastructure you operate may be passed with `trusted=True`. An untrusted
*pass* therefore earns zero points, and an untrusted *failure* earns fewer
points than a verified one.

**Missing evidence is unknown, not malicious.** No `Authentication-Results`
header produces no signal — see `tests/test_authentication_signals.py`.

**Known false positives.** Shared-SaaS senders whose `Return-Path` legitimately
differs from the visible `From` (bulk mail providers, mailing lists, forwarders)
will trip the Return-Path rule. That is inherent to header analysis without
DMARC alignment evaluation, which is **not implemented**.

---

## BEC analyzer (`services/bec_analyzer.py`)

| Signal | Detection | Points |
|---|---|---|
| Financial fraud | `wire transfer`, `bank transfer`, `gift cards`, `cryptocurrency`, `bitcoin`, `routing number`, `invoice … overdue/payment`, `update … payment details`, `change … bank details` | 6 |
| Executive impersonation | `ceo`, `cfo`, `board`, `executive`, `managing director`, `i am the/your ceo/cfo/boss/manager` | 5 |
| Secrecy pressure | `keep this confidential`, `do not tell/inform/discuss`, `between us`, `urgent … secret`, `handle this discreetly` | 5 |
| Credential harvesting | `verify … password/account/login/credential`, `(password|credential) … expired/suspended/blocked/deactivated`, `click … verify/confirm/update … account/password/login` | 6 |

**Known false positives — pinned in tests, not hidden.** These are keyword
patterns, so routine corporate language matches: `board` fires on an ordinary
"review the board deck", and a legitimate finance email saying "wire transfer"
matches the financial rule. The design absorbs this rather than pretending
otherwise: BEC contributes at most 15 points locally and at most 10 through the
evidence channel, and a `Phishing Email` verdict requires the model
probability and the other channels to agree. `tests/test_bec_signals.py` pins
the `board` false positive explicitly so tightening a pattern is a deliberate,
reviewed change.

**Not implemented.** Payroll-change and vendor-impersonation detection require
entity resolution against a directory, and "unusual payment instruction" needs
history. Out of scope for a stateless text analyzer.

---

## What is deliberately *not* a signal

- **Model `prediction`** (`phishing` / `legitimate`) is reported but the risk
  score starts from `phishing_probability`, not `max(predicted class)`. A 96%
  *legitimate* email contributes ~4 points, not ~96.
- **AI explanations.** LLM output never changes the verdict, the risk score or
  the evidence list; it is only attached when it agrees to be described as
  `deterministic`. See `docs/API_Documentation.md`.
- **Attachment names / metadata.** Parsed and reported, never scored.
- **URL destination content.** Not fetched by default. The opt-in live path is
  guarded by `services/url_safety.py` (52 tests in `tests/test_url_safety.py`
  covering scheme/port/credential rejection, private and internal targets, the
  cloud metadata endpoint, dual-homed hosts, tunneled IPv6, redirect
  revalidation and the response cap).