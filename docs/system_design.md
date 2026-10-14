# System Design

## Runtime topology

```
Browser ──► Nginx (:80) ──┬──► SPA (static /usr/share/nginx/html, SPA fallback)
                           └──► /api/* ──► backend:8000 (uvicorn)
                                                ├── trained_models/ (read-only mount)
                                                └── /data/*.db (persistent volume)
```

- `docker-compose.yml` defines `backend` (port 8000) and `frontend`
  (Nginx on port 3000→80). The Nginx config proxies `/api/` to the backend,
  so same-origin deployments work without CORS changes.
- The backend image ships code only. Model artifacts (`trained_models/`)
  are mounted read-only at runtime — they are gitignored binaries, not build
  inputs. Supply them by mounting a versioned artifact directory or a
  release-asset download step.
- SQLite lives at `DATABASE_PATH` (`/data/phishing_detection.db` in
  Compose) on the `phishing-data` named volume, so restarts keep history.
- Healthchecking hits `/ready` (model artifacts present), not just `/health`
  (process alive).

## Environments

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` | API origin baked into the SPA at build time. Override per environment (`--build-arg`). |
| `VITE_API_KEY` | _(empty)_ | Sent as `X-API-Key` by the SPA when the backend sets `API_KEYS`. |
| `API_KEYS` | _(empty = open dev mode)_ | Comma-separated keys gating history/dashboard/analytics/feedback. |
| `AI_EXPLANATIONS_ENABLED` | `true` | `false` = local-only mode; no email content leaves the server. |
| `OPENROUTER_API_KEY` | — | External explanation provider. Unset also forces local-only mode. |
| `DATABASE_PATH` | `./phishing_detection.db` | SQLite file location. |
| `MODEL_DIR` | `trained_models/` | Artifact directory expected by the backend image. |

See `.env.example` for the full template.

## Request lifecycle protections

1. **Body cap** — >200KB JSON bodies rejected (413) before parsing; uploads
   have their own 2MB file cap with type allow-list (415/413/422).
2. **Rate limiting** — 60 req/min per IP on `/api/*`, bounded memory
   (oldest buckets evicted past 5,000 clients). Single-instance design: for
   multi-worker/replica deployments, move enforcement to Redis or the
   gateway. Behind a proxy, configure trusted `X-Forwarded-For` handling.
3. **Provider isolation** — the LLM call has a 10s timeout and 1 retry, runs
   synchronously off the verdict path, and any failure degrades to the
   deterministic result. The verdict never depends on the provider.
4. **CORS** — allow-list limited to local dev origins; extend explicitly for
   hosted frontends.

## Scaling notes

- Inference is CPU-bound TF-IDF + a 200-tree forest (~hundreds of ms). Scale
  horizontally with more uvicorn workers behind the existing `/ready` check;
  pair with a shared rate limiter (see above) and a client-side or DB-backed
  result cache keyed by `email_hash`.
- The bulk retrain (`ai-engine/training/train_model.py`) is an offline batch
  job, not part of serving. Publish new artifacts with
  `trained_models/model_metadata.json` and roll them via the read-only mount.

## Known limitations (by design, for now)

- No SPF/DKIM cryptographic verification — the auth analyzer reads
  caller-supplied `Authentication-Results`, it does not validate signatures.
- No live URL fetching / redirect-chain analysis (would require SSRF-safe
  outbound controls: protocol allow-list, private-IP/DNS-rebinding guards).
- No per-user history isolation — add authentication + tenant scoping before
  multi-user production use. See [Security](security.md).
