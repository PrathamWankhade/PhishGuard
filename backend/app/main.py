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

# Stricter quota for expensive inference/upload routes (abuse control on the
# public scanning surface; gateway/Redis still needed for multi-worker).
EXPENSIVE_PATHS = ("/api/v1/predict", "/api/v1/upload")
EXPENSIVE_RATE_LIMIT = 30
expensive_limit_store: dict = defaultdict(list)


def _bucket_hit(store, key: str, now: float) -> list:
    window_start = now - RATE_LIMIT_WINDOW
    return [t for t in store.get(key, []) if t > window_start]


def check_rate_limit(client_ip: str, path: str, now: float | None = None) -> bool:
    """Return True if the request is allowed, recording it. Unit-testable."""
    now = now if now is not None else time.time()
    if path in EXPENSIVE_PATHS:
        bucket = _bucket_hit(expensive_limit_store, client_ip, now)
        if len(bucket) >= EXPENSIVE_RATE_LIMIT:
            expensive_limit_store[client_ip] = bucket
            return False
        bucket.append(now)
        expensive_limit_store[client_ip] = bucket
    bucket = _bucket_hit(rate_limit_store, client_ip, now)
    if len(bucket) >= RATE_LIMIT:
        rate_limit_store[client_ip] = bucket
        return False
    bucket.append(now)
    rate_limit_store[client_ip] = bucket
    for store in (rate_limit_store, expensive_limit_store):
        if len(store) > MAX_TRACKED_CLIENTS:
            store.pop(next(iter(store)), None)
    return True

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
        # Full inference contract (what production scoring actually needs):
        # predict + predict_proba, a phishing class, and a valid probability.
        assert hasattr(model, "predict") and hasattr(model, "predict_proba")
        classes = [str(c) for c in list(model.classes_)]
        assert "phishing" in classes, f"model classes {classes} lack 'phishing'"
        proba = model.predict_proba(vectorizer.transform(["readiness probe"]))
        p = float(proba[0][classes.index("phishing")])
        assert 0.0 <= p <= 1.0, f"phishing probability out of range: {p}"
        return True, {"model_classes": classes}
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
        if not check_rate_limit(client_ip, request.url.path):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again later."})
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
