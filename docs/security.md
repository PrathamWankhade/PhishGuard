# Security

Threat model: this service accepts adversarial email content (attackers craft
the input) and optionally forwards excerpts to an external LLM. Defenses are
layered accordingly.

## Trust boundaries

- **Email text is untrusted input.** It is sanitized (control chars stripped,
  length-capped) and never executed, never interpolated into prompts as
  instructions — the LLM system prompt treats it as data to summarize, and
  the LLM cannot change the verdict in any case.
- **Attachments are never executed.** Only metadata (filename, MIME type,
  size) is extracted. Deeper inspection belongs in an isolated sandbox,
  not in this service.
- **URLs are never fetched.** Analysis is lexical (hostname normalization,
  TLD/shortener/IP/subdomain rules, mixed-script detection). Live
  reputation or redirect-chain analysis requires SSRF-safe outbound
  controls first: protocol allow-list, private/loopback/link-local blocks,
  DNS-rebinding guards, redirect ceilings.

## Authentication and privacy

- Sensitive routes (`/history`, `/dashboard`, `/analytics/*`, `/feedback*`)
  accept an API-key gate via `Depends(require_api_key)`. Set `API_KEYS` in
  production; without it the server runs in open dev mode.
- The SPA's `VITE_API_KEY` is public by construction (bundled JS). Treat it
  as a shared-client convenience for single-operator deployments, never as a
  user-authentication boundary. Multi-user production needs session auth or a
  backend-for-frontend plus per-user history isolation (not implemented).
- Per-user history isolation is **not yet implemented** — do not store
  multiple users' mail without adding authentication + tenant-scoped queries.
- External AI processing sends up to 2,000 characters per scan to OpenRouter.
  Disclosure is documented in `openrouter_explainer.py`; operators should
  surface it in product copy. `AI_EXPLANATIONS_ENABLED=false` (or an unset
  API key) gives a local-only mode with zero external data flow.
- Stored scan rows contain raw bodies and senders: define retention and
  deletion before production use (see
  [Database Design](database_design.md)).

## Abuse and resource controls

| Control | Setting |
|---|---|
| Body cap | 200KB JSON (413); uploads 2MB with type allow-list |
| Field caps | 10k text, 500 sender/reply fields, 2k auth-results |
| Rate limit | 60/min/IP on `/api/*`, bounded buckets (Redis/gateway for multi-worker) |
| Provider call | 10s timeout, 1 retry, verdict-independent |
| Upload parsing | 2MB raw cap, 50k body cap, never raises |

## Operational honesty

- `/health` = liveness; `/ready` = model readiness. Wire load balancers and
  Docker healthchecks to `/ready`.
- The model loader fails loudly at inference time if artifacts are missing;
  the API never returns a fabricated safe verdict.
- History/dashboard responses contain no demo data; the frontend's Demo Mode
  badge marks fallback numbers as non-production.
