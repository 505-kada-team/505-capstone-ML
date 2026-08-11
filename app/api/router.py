from fastapi import APIRouter

from app.api.endpoints.prediction import router as prediction_router

api_router = APIRouter()
api_router.include_router(prediction_router, prefix="", tags=["prediction"])
