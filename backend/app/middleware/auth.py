import hashlib
import os
from fastapi import Header, HTTPException


def _configured_keys() -> set[str]:
    raw = os.environ.get("API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def _owner_for_key(x_api_key: str | None) -> str:
    """Map a (possibly absent) API key to a stable, non-secret owner id.

    Returns ``"anonymous"`` in dev mode (no keys configured) or when no valid
    key is supplied, so every request shares one tenant — matching the
    previous single-tenant behaviour. When keys are configured, returns a
    short hash of the validated key so different operators never see each
    other's scan history, dashboard KPIs, or analytics.
    """
    allowed = _configured_keys()
    if not allowed:
        return "anonymous"
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key not in allowed:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()[:16]


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """Gate sensitive routes when API_KEYS is configured.

    Dev mode (API_KEYS unset): allow all, matching previous behaviour.
    Production: set API_KEYS=key1,key2 and clients must send X-API-Key.

    Returns the resolved owner id for the caller (used to scope history,
    dashboard and analytics per operator).
    """
    return _owner_for_key(x_api_key)


def optional_owner(x_api_key: str | None = Header(default=None)) -> str:
    """Resolve an owner id without gating: invalid/missing keys fall back to
    the shared ``"anonymous"`` tenant. Used by the public /predict endpoint
    so scans made with a key are isolated to that operator while unauthed
    scans stay shared."""
    allowed = _configured_keys()
    if not allowed or x_api_key is None or x_api_key not in allowed:
        return "anonymous"
    return hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()[:16]
