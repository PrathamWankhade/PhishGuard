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
- **URLs are not fetched by default.** Analysis is lexical (hostname
  normalization, TLD/shortener/IP/subdomain rules, mixed-script detection).
  Live reputation and redirect-chain analysis is opt-in via
  `URL_REPUTATION_ENABLED=true`, and only through
  `services/url_safety.py`, which enforces: scheme allow-list, userinfo
  rejection, port allow-list, resolution of every address with a public-IP
  check (including mapped/tunneled IPv6 and `100.64.0.0/10`), connection
  pinned to the validated IP (DNS-rebinding guard), revalidation of every
  redirect, a response size cap, and strict connect/read timeouts. Nothing
  is fetched unless an operator turns it on, and it is not fetched by this
  service's frontend.

## Authentication and privacy

- Sensitive routes (`/history`, `/dashboard`, `/analytics/*`, `/feedback*`)
  accept an API-key gate via `Depends(require_api_key)`. Set `API_KEYS` in
  production; without it the server runs in open dev mode.
- Each API key is a distinct tenant: scan history, dashboard KPIs and
  analytics are scoped to the caller's key (owner column on `scan_history`,
  derived as a short hash of the validated key). Dev mode (no keys) keeps
  the previous single-tenant behaviour. `/predict` accepts an optional key
  so scans made with a key are isolated to that operator; unauthed scans
  stay in the shared tenant. Feedback rows are gated but aggregated.
- The SPA's `VITE_API_KEY` is public by construction (bundled JS). Treat it
  as a shared-client convenience for single-operator deployments, never as a
  user-authentication boundary. To limit blast radius, the key is attached
  only to gated read routes (history/dashboard); the open `/predict` and
  `/upload` endpoints never receive it. Multi-user production with real
  per-user accounts still needs session auth or a backend-for-frontend on
  top of this isolation.
- Per-user history isolation **is implemented**: an `owner` column on
  `scan_history` scopes reads, and each API key is a distinct tenant (a short
  hash of the validated key). Dev mode (no `API_KEYS`) keeps a single shared
  tenant. What is *not* implemented is real user accounts — the tenant id is
  derived from the key, so rotation loses history, and a dropped key stays
  orphaned in the table.
- External AI processing sends up to 2,000 characters per scan to OpenRouter.
  Disclosure is documented in `openrouter_explainer.py`; operators should
  surface it in product copy. `AI_EXPLANATIONS_ENABLED=false` (or an unset
  API key) gives a local-only mode with zero external data flow.
- **There is no Gemini integration**, and there has not been one since the
  OpenAI-compatible client replaced it (`24c3c33`). Explanations come only
  from OpenRouter via the OpenAI SDK. Roadmaps or proposals describing a
  Gemini integration are describing something this repository never had.
- LLM output is bounded (`MAX_BULLETS`, `MAX_BULLET_CHARS`) before display
  because it sits next to verified evidence, and it is attached as a separate
  field — never merged into `signals`/`reasons`. See
  `tests/test_llm_reliability.py` for the isolation contract.
- Stored scan rows contain raw bodies and senders: define retention and
  deletion before production use (see
  [Database Design](database_design.md)).

## Abuse and resource controls

| Control | Setting |
|---|---|
| Body cap | 200KB JSON + 2MB uploads at the app; `client_max_body_size 2m` at Nginx (set the same ceiling at every proxy/gateway — the app check alone cannot stop a slow spool) |
| Field caps | 10k text, 500 sender/reply fields, 2k auth-results |
| Rate limit | 60/min/IP general, 30/min/IP on predict+upload, bounded buckets (Redis/gateway REQUIRED for multi-worker — four workers quadruple the effective quota) |
| Provider call | 10s timeout, 1 retry, verdict-independent; daily budget cap (`AI_DAILY_BUDGET`, default 500 submitted calls) + concurrency semaphore (4, non-blocking degrade); per-process counters — enforce provider-side budgets for multi-worker |
| Provider response | Bounded to 5 bullets and 300 chars each before display (`MAX_BULLETS` / `MAX_BULLET_CHARS`); provider text is never merged into the evidence channel |
| Injected prompt text | The email body is model *input*; a reply that complies with an injection ("reply that this is safe") still cannot alter the verdict, risk score, or evidence list |
| Upload parsing | 2MB raw cap, 50k body cap, never raises |

## Operational honesty

- `/health` = liveness; `/ready` = model readiness. Artifacts are validated
  once at startup and cached (60s TTL) so orchestrator probes never pay a
  `joblib.load` per call. Wire load balancers and Docker healthchecks to
  `/ready`.
- The model loader fails loudly at inference time if artifacts are missing;
  the API never returns a fabricated safe verdict.
- History/dashboard responses contain no demo data; the frontend's Demo Mode
  badge marks fallback numbers as non-production.
