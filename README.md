# Email Phishing Detection System

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=flat-square&logo=scikit-learn)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

A full-stack platform for phishing email detection: React scanner and
analytics dashboard, FastAPI backend, scikit-learn text classifier with
URL/sender/authentication/fraud signals, and optional LLM explanations.
Built around one principle: **every verdict is traceable to evidence, and
every score means exactly what the interface says it means.**

- Raw model probability and heuristic risk score are separate fields, never
  conflated.
- Deterministic evidence is never overwritten by AI-generated text.
- The UI never presents a heuristic estimate as an ML verdict.

## Quick start

Prerequisites: Python 3.11+, Node.js 20+, and (optionally) an OpenRouter API
key for AI explanations. Without the key the system runs in local-only mode.

```bash
# Backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows  |  source .venv/bin/activate  (Linux/Mac)
pip install -r requirements.txt
cp .env.example .env              # set OPENROUTER_API_KEY, API_KEYS as needed
uvicorn backend.app.main:app --reload     # http://127.0.0.1:8000, docs at /docs

# Frontend
npm install
npm run dev                       # http://localhost:3000

# Tests
pytest tests/ -v

# Docker (frontend :3000, API :8000)
docker compose up --build
```

## How detection works

```
Paste text / upload .eml
  -> server-side MIME parsing (sender, subject, body, URLs, attachments)
  -> TF-IDF + soft-voting ensemble (LogisticRegression + RandomForest)
  -> URL / sender / auth / BEC analyzers (bounded, evidence-tagged)
  -> decision engine: risk_score -> verdict (Safe / Suspicious / Phishing)
  -> deterministic signals (+ optional AI summary) -> scan record
```

The model outputs a binary class and probability. Analyzers add capped risk
points (URLs <= 20, sender <= 30, auth/fraud evidence <= 10). The verdict
follows documented thresholds (>= 75 Phishing, >= 45 Suspicious). Full field
semantics: [docs/API_Documentation.md](docs/API_Documentation.md).

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Enables AI summaries; unset = local-only, nothing leaves the server |
| `AI_EXPLANATIONS_ENABLED` | `true` | `false` forces local-only mode |
| `API_KEYS` | _(empty = open dev)_ | Gates history/dashboard/analytics/feedback via `X-API-Key` |
| `VITE_API_BASE_URL` / `VITE_API_KEY` | local / empty | API origin and key baked into the SPA at build time |
| `DATABASE_PATH` | `./phishing_detection.db` | SQLite location (persisted volume in Docker) |

## API overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/predict` | Classify an email (optional header evidence fields) |
| `POST` | `/api/v1/upload` | Server-side `.eml` parsing with validation |
| `GET` | `/api/v1/history` | Scan history (auth-gated) |
| `GET` | `/api/v1/dashboard` | KPI aggregates with explicit unique-vs-event counts (auth-gated) |
| `POST`/`GET` | `/api/v1/feedback`(`/stats`) | Analyst review loop (auth-gated) |
| `GET` | `/health` · `/ready` | Liveness vs model-readiness probes |

Details and response contract: [docs/API_Documentation.md](docs/API_Documentation.md).

## Evaluation

Metrics (precision/recall/F1, false-positive/negative rates, log loss,
Brier) are produced by `train_model.py` / `evaluate_model.py` /
`source_split_eval.py` and recorded per release in
`trained_models/model_metadata.json`. Cross-validation runs inside a sklearn
Pipeline (no preprocessing leakage); source-separated evaluation holds out
entire campaigns. Protocol: [docs/model_evaluation.md](docs/model_evaluation.md).

## Documentation

- [Architecture](docs/architecture.md) — layers, decision engine, patterns
- [System Design](docs/system_design.md) — deployment, environments, scaling
- [Workflow](docs/workflow.md) — scan, upload, analytics, feedback, retrain
- [Database Design](docs/database_design.md) — schema and counting semantics
- [Security](docs/security.md) — auth, privacy, abuse controls
- [Model Evaluation](docs/model_evaluation.md) — metrics and protocol

## Project structure (essentials)

```
frontend/src/          # React SPA (Scanner, Dashboard, UploadEmail, api.js)
backend/app/
  api/routes/          # predict, upload, history, dashboard, analytics, feedback
  services/            # phishing_detector (decision engine), url/sender/auth/bec
  utils/email_parser.py# standards-aware MIME parsing
  middleware/auth.py   # optional API-key gate
ai-engine/training/    # build_final_dataset, train_model, evaluate, source_split_eval
tests/                 # phase1/phase2/phase3 contract tests + unit suites
docker/ + compose      # backend image, SPA + Nginx, volumes, healthchecks
```

## Status and roadmap

Done: unified verdict contract, URL evidence model, explicit unavailable
states, explanation resilience, Pipeline-CV training, full-text dataset
dedup, MIME parsing, upload validation, dashboard semantics, Docker
readiness, API-key gating, auth/BEC signals, feedback loop, CI pipeline
(`backend` model-independent tests + `frontend` production build).

Next: per-user history isolation, Redis-backed rate limiting, SSRF-safe URL
reputation, transformer benchmark on the frozen test set.

## Author

**Pratham Wankhade** — [GitHub](https://github.com/PrathamWankhade) ·
[LinkedIn](https://www.linkedin.com/in/pratham-wankhade)

*Built as a production-style cybersecurity engineering project: measurable
detection, traceable evidence, honest interfaces.*
