# Database Design

Engine: SQLite with WAL mode (`PRAGMA journal_mode=WAL`), auto-initialized
on startup via `init_db()`. Production path is configurable through the
`DATABASE_PATH` environment variable (the Docker Compose setup persists it
on a named volume — see [System Design](system_design.md)).

## `scan_history` — canonical emails + scan events in one row

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Internal row id |
| `email_hash` | TEXT UNIQUE | MD5 of normalized text + sender; canonical-email key |
| `sender` | TEXT | Sender as submitted |
| `email_text` | TEXT | Sanitized body (≤10k chars) |
| `prediction` | TEXT | Final verdict label (Safe / Suspicious / Phishing Email) |
| `confidence` | REAL | Risk score at scan time (legacy name; see API docs) |
| `risk_level` | TEXT | `high` / `medium` / `low` |
| `reasons` | TEXT (JSON) | Deterministic signals serialized as a JSON list |
| `scan_count` | INTEGER | Incremented on rescan of the same hash |
| `created_at` | TIMESTAMP | Last-scan time (bumped on rescan) |

**Two measures, one table.** A row is a *canonical email*; `scan_count` is
the number of *scan events* for it. Dashboards must pick explicitly:

- unique emails → `COUNT(*)`
- scan events → `SUM(scan_count)`

The `/dashboard` endpoint returns both (`unique_emails`,
`total_scan_events`) so clients cannot mix them up.

Schema migrations are additive (`PRAGMA table_info` checks before
`ALTER TABLE`), so existing databases upgrade without data loss.

## `scan_feedback` — analyst reviews (separate table, separate meaning)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Review id |
| `email_hash` | TEXT | Links to `scan_history.email_hash` |
| `verdict_correct` | INTEGER | 1 = analyst agrees, 0 = analyst disputes |
| `true_label` | TEXT | Analyst's corrected label (optional) |
| `notes` | TEXT | Free-text rationale (≤2000 chars) |
| `created_at` | TIMESTAMP | Review time |

Feedback rows are **monitoring data, not training data**. They feed the
`/feedback/stats` error-rate metric. Promoting them into a training set
requires a separate human-review step — unreviewed feedback must never be
treated as ground truth (it inherits the same biases as the reporters).

## Privacy notes

Stored rows contain raw email bodies and sender addresses. Before storing
real users' mail: enable `API_KEYS`, scope history per user/tenant (not yet
implemented — history is currently global), define a retention/deletion
policy, and consider encrypting `email_text` at rest. See
[Security](security.md).

**Default retention policy:** `scan_history` rows older than 90 days are
deleted; `scan_feedback` rows are kept 365 days for trend monitoring.
Enforce with `python scripts/purge_history.py --dry-run` (preview) and
`--apply` (delete). Schedule it via cron/systemd/Task Scheduler in
production; document any deviation for your deployment.
