import time
import re
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.api.routes.history import router as history_router
from backend.app.api.routes.dashboard import router as dashboard_router
from backend.app.config.constants import API_PREFIX
from backend.app.database.db import init_db

rate_limit_store = defaultdict(list)
RATE_LIMIT = 60
RATE_LIMIT_WINDOW = 60
MAX_TRACKED_CLIENTS = 5000


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("SQLite database initialized")
    yield


app = FastAPI(
    title="AI Phishing Detection API",
    version="2.0.0",
    description="AI-powered phishing email detection system using Machine Learning, NLP, FastAPI and SQLite",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        # Trust X-Forwarded-For only when set by a configured proxy is out of
        # scope for Phase 1; document that proxy deployments must configure it.
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        bucket = [t for t in rate_limit_store.get(client_ip, []) if t > window_start]
        if len(bucket) >= RATE_LIMIT:
            rate_limit_store[client_ip] = bucket
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again later."})
        bucket.append(now)
        rate_limit_store[client_ip] = bucket
        # Bound memory: evict oldest client buckets when too many are tracked.
        if len(rate_limit_store) > MAX_TRACKED_CLIENTS:
            oldest = next(iter(rate_limit_store))
            rate_limit_store.pop(oldest, None)
    return await call_next(request)


@app.get("/")
def root():
    return {
        "message": "AI Phishing Detection API Running",
        "docs": "/docs",
        "version": "2.0.0",
        "dashboard": "/api/v1/dashboard",
    }


@app.get("/health")
def health():
    # Liveness only: process is running. See /ready for model readiness.
    return {"status": "healthy", "service": "phishing-detection-api", "version": "2.0.0"}


@app.get("/ready")
def ready():
    """Readiness: verify model artifacts exist and are loadable."""
    from pathlib import Path

    base = Path(__file__).resolve().parents[3]
    model_path = base / "trained_models" / "phishing_model.pkl"
    vectorizer_path = base / "trained_models" / "tfidf_vectorizer.pkl"
    model_ok = model_path.exists() and vectorizer_path.exists()
    status = "ready" if model_ok else "not_ready"
    code = 200 if model_ok else 503
    return JSONResponse(
        status_code=code,
        content={
            "status": status,
            "model_loaded": model_ok,
            "model_path": str(model_path),
            "vectorizer_path": str(vectorizer_path),
        },
    )


app.include_router(api_router, prefix=API_PREFIX)
app.include_router(history_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
