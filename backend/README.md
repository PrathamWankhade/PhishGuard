# Backend — FastAPI Phishing Detection Server

FastAPI-powered REST API server that serves the ML model, manages scan history, and integrates with OpenRouter for AI-powered explanations.

## Directory Layout

```
backend/
└── app/
    ├── api/                    # Route layer
    │   ├── router.py           # Aggregates all route modules
    │   └── routes/
    │       ├── prediction.py   # POST /api/v1/predict — core scanning endpoint
    │       ├── dashboard.py    # GET  /api/v1/dashboard — aggregated stats
    │       └── history.py      # GET  /api/v1/history — full scan history
    ├── database/               # Persistence layer
    │   ├── db.py               # SQLite connection (WAL mode, auto-init)
    │   ├── schema.py           # Table definitions + migration support
    │   └── models.py           # CRUD operations (insert, query, update)
    ├── services/               # Business logic
    │   ├── phishing_detector.py    # Decision engine: model + analyzers -> verdict
    │   ├── url_analyzer.py         # Per-URL findings, hostname normalization
    │   ├── sender_analyzer.py      # Domain blocklist validation
    │   ├── auth_analyzer.py        # Reply-To / SPF / DKIM / DMARC signals
    │   ├── bec_analyzer.py         # Fraud-pattern signals
    │   ├── openrouter_explainer.py # LLM explanation via OpenRouter API (lazy client)
    │   └── explanation_engine.py   # Aggregates explanations
    ├── middleware/             # CORS, rate limiting, error handling
    ├── config/                 # Environment configuration
    ├── controllers/            # Thin handler layer
    ├── utils/                  # Shared helpers
    └── main.py                 # FastAPI app entrypoint with lifespan
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/predict` | Analyze email text + sender for phishing |
| `GET` | `/api/v1/dashboard` | Aggregated scan statistics |
| `GET` | `/api/v1/history` | Full scan history with AI reasons |
| `GET` | `/health` | Health check |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for AI explanations |
| `DATABASE_PATH` | No | Path to SQLite DB file (default: `phishing_detection.db`) |
| `MODEL_PATH` | No | Path to model pickle (default: `trained_models/`) |

## Running

```bash
uvicorn backend.app.main:app --reload
```

Server starts at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.
