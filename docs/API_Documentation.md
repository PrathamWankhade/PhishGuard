# API Documentation

Base URL (local dev): `http://127.0.0.1:8000`. All product routes live under
`/api/v1`. Interactive docs: `/docs`.

Authentication: when the server sets `API_KEYS`, clients must send
`X-API-Key: <key>` on `/history`, `/dashboard`, `/analytics/*`, and
`/feedback*`. When `API_KEYS` is unset (dev mode), these routes are open.
The frontend sends the key automatically from `VITE_API_KEY`.

## POST `/api/v1/predict`

Analyze an email for phishing indicators.

Request:

```json
{
  "email_text": "Urgent: verify your password now.",
  "sender": "support@example.xyz",
  "reply_to": "",
  "return_path": "",
  "auth_results": ""
}
```

Only `email_text` is required (non-empty, ≤10,000 chars after sanitization;
bodies above 200KB are rejected with 413). `reply_to`, `return_path`, and
`auth_results` are optional header evidence — pass them through from
`POST /upload` when available.

Response (`200`, `status: "completed"`):

```json
{
  "status": "completed",
  "label": "Phishing Email",
  "verdict": "Phishing Email",
  "prediction": "phishing",
  "model_prediction": "phishing",
  "model_confidence": 88.4,
  "confidence": 96.4,
  "risk_score": 96.4,
  "risk_level": "high",
  "reasons": ["Sender uses a suspicious top-level domain", "..."],
  "signals": ["Sender uses a suspicious top-level domain", "..."],
  "ai_explanation": ["..."],
  "explanation_source": "ai",
  "source": "backend-ai-engine",
  "policy_version": "phase3-evidence-v2",
  "email_hash": "9f2c..."
}
```

Field semantics:

- `model_prediction` / `model_confidence` — raw classifier output. A binary
  class (`phishing` / `legitimate`) and its probability. Never overwritten.
- `risk_score` — heuristic policy score (0–99). **Not a calibrated
  probability**; do not display it with probability language.
- `confidence` — legacy alias of `risk_score`, kept for existing clients.
  New clients should use `model_confidence` / `risk_score`.
- `verdict` / `label` — final Safe / Suspicious / Phishing decision.
- `signals` / `reasons` — deterministic evidence strings (identical lists).
- `ai_explanation` — supplementary LLM summary, or `null` in local-only
  mode / on provider failure. `explanation_source` is `"ai"` or
  `"deterministic"`.

Errors: `422` empty text · `413` oversized body · `429` rate limited.
The endpoint never returns a fake successful prediction: if the model cannot
load, `/ready` reports `not_ready` (503).

## POST `/api/v1/upload`

Parse a raw email file server-side (preferred over browser parsing).

- Multipart form field `file`; accepted types `.eml`, `.txt`, `.msg`;
  2MB limit (`413`), empty file (`422`), wrong type (`415`).
- Response: `{ sender, subject, reply_to, return_path, body, urls,
  attachments[{filename, content_type, size_bytes}], errors[] }`.
- Malformed messages never raise: the parser returns what it could extract
  plus `errors[]` describing what failed.

## GET `/api/v1/history`

Scan history, newest first: `[{ id, sender, prediction, confidence,
risk_level, reasons[], scan_count, created_at }]`. A `scan_count > 1` means
the same canonical email was rescanned. (Auth-gated — see above.)

## GET `/api/v1/dashboard`

Aggregated KPIs computed from the database (never demo data):

```json
{
  "unique_emails": 120,
  "total_scan_events": 145,
  "total_scans": 120,
  "phishing_count": 30,
  "suspicious_count": 12,
  "safe_count": 78,
  "avg_confidence": 81.4,
  "risk_levels": { "high": 30, "medium": 12, "low": 78 }
}
```

`unique_emails` (canonical rows) and `total_scan_events` (Σ `scan_count`)
are distinct measures — use the one your KPI defines. (Auth-gated.)

## GET `/api/v1/analytics/summary`

`{ scanned_emails, phishing_detected, average_confidence, suspicious_urls }`
— lightweight counters for ops views. (Auth-gated.)

## POST `/api/v1/feedback` · GET `/api/v1/feedback/stats`

Analyst review loop. `POST` accepts `{ email_hash, verdict_correct,
true_label?, notes? }` and stores it in a table separate from scan history.
`GET` returns `{ total_reviews, reported_errors, reported_error_rate }`.
Reviewed labels are monitoring data, **not** training labels. (Auth-gated.)

## GET `/health` · GET `/ready`

- `/health` — liveness only (`{"status": "healthy", ...}`). Use for
  "is the process up".
- `/ready` — readiness: verifies model artifacts exist (`200 ready` /
  `503 not_ready`). Use for load-balancer checks and Docker healthchecks.
- `/api/v1/health` — legacy route returning `{"status": "ok"}`.

## Frontend contract notes

- `scanEmail()` throws on any backend failure. Callers must show an explicit
  unavailable state — the heuristic estimator (`heuristicEstimate()`) is an
  opt-in demo helper whose output is tagged `status: "heuristic-only"` with a
  warning, never an ML result.
- The dashboard shows a `Demo Mode` badge whenever live data is unreachable,
  so fallback numbers are never mistaken for production metrics.
