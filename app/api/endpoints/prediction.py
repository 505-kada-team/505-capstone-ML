from fastapi import APIRouter, HTTPException

from app.schemas.prediction import MenuRecommendation, PlanRequest
from app.services.prediction import build_recommendations

router = APIRouter()


@router.post("/predict-assortment", response_model=list[MenuRecommendation])
def predict_assortment(payload: PlanRequest):
    try:
        recommendations = build_recommendations(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return recommendations
