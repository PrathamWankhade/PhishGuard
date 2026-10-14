from fastapi import APIRouter
from backend.app.api.routes import (
    analytics,
    feedback,
    health,
    prediction,
    upload,
    history
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(prediction.router)
api_router.include_router(upload.router)
api_router.include_router(analytics.router)
api_router.include_router(history.router)
api_router.include_router(feedback.router)