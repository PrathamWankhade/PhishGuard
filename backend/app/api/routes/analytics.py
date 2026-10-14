from fastapi import APIRouter, Depends
from backend.app.controllers.analytics_controller import get_summary
from backend.app.middleware.auth import require_api_key

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", dependencies=[Depends(require_api_key)])
def summary() -> dict:
    return get_summary()
