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
# Reject oversized request bodies before parsing (upload route has its own 2MB file cap).
MAX_BODY_BYTES = 200_000

# Cached readiness: artifacts are validated once (or on TTL expiry), not
# joblib-loaded on every orchestrator probe.
import threading as _threading

_ready_cache = {"at": 0.0, "ok": False, "detail": {}}
_ready_lock = _threading.Lock()
READY_TTL_SECONDS = 60


def _evaluate_readiness() -> tuple[bool, dict]:
    """Load artifacts and return (ok, detail). Slow path — call under cache."""
    from pathlib import Path

    # backend/app/main.py -> parents[2] is the repository root.
    base = Path(__file__).resolve().parents[2]
    model_path = base / "trained_models" / "phishing_model.pkl"
    vectorizer_path = base / "trained_models" / "tfidf_vectorizer.pkl"
    if not (model_path.exists() and vectorizer_path.exists()):
        return False, {"reason": "artifacts missing"}
    try:
        import joblib

        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
        assert hasattr(model, "predict") and hasattr(model, "classes_")
        vectorizer.transform(["readiness probe"])
        return True, {"model_classes": [str(c) for c in list(model.classes_)]}
    except Exception as e:
        return False, {"reason": f"artifact load failed: {e}"}


def get_readiness() -> tuple[bool, dict]:
    now = time.time()
    with _ready_lock:
        if now - _ready_cache["at"] < READY_TTL_SECONDS and _ready_cache["at"] > 0:
            return _ready_cache["ok"], _ready_cache["detail"]
    ok, detail = _evaluate_readiness()
    with _ready_lock:
        _ready_cache.update({"at": time.time(), "ok": ok, "detail": detail})
    return ok, detail


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("SQLite database initialized")
    ok, detail = get_readiness()  # pre-warm readiness cache at startup
    print(f"Model readiness: {'ready' if ok else 'NOT READY'} {detail}")
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
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


@app.middleware("http")
async def size_limit_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT") and request.url.path.startswith("/api/"):
        clen = request.headers.get("content-length")
        if clen and clen.isdigit() and int(clen) > MAX_BODY_BYTES:
            # Upload route accepts up to 2MB files; let it enforce its own cap.
            if not request.url.path.startswith("/api/v1/upload"):
                return JSONResponse(status_code=413, content={"detail": "Request body too large."})
    return await call_next(request)


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
    """Readiness from the cached model-service state (validated at startup,
    re-validated at most every READY_TTL_SECONDS)."""
    ok, detail = get_readiness()
    if not ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "model_loaded": False, **detail},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "model_loaded": True, **detail},
    )


app.include_router(api_router, prefix=API_PREFIX)
app.include_router(history_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
