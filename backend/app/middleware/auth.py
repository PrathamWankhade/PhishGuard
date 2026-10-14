import os
from fastapi import Header, HTTPException


def _configured_keys() -> set[str]:
    raw = os.environ.get("API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Gate sensitive routes when API_KEYS is configured.

    Dev mode (API_KEYS unset): allow all, matching previous behaviour.
    Production: set API_KEYS=key1,key2 and clients must send X-API-Key.
    """
    allowed = _configured_keys()
    if not allowed:
        return
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key not in allowed:
        raise HTTPException(status_code=403, detail="Invalid API key")
