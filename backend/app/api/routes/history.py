import json
from fastapi import APIRouter, Depends

from backend.app.database.models import get_scan_history
from backend.app.middleware.auth import require_api_key

router = APIRouter()


@router.get("/history")
def get_history(owner: str = Depends(require_api_key)):
    results = get_scan_history(owner=owner)
    return [
        {
            "id": row.get("id"),
            "sender": row.get("sender", ""),
            "prediction": row.get("prediction", ""),
            # Stored column is named `confidence` for historical reasons but
            # holds the policy risk score; expose it under its honest name.
            "risk_score": row.get("confidence", 0),
            "risk_level": row.get("risk_level", "low"),
            "reasons": json.loads(row["reasons"]) if row.get("reasons") else [],
            "scan_count": row.get("scan_count", 1),
            "created_at": row.get("created_at", ""),
        }
        for row in results
    ]
