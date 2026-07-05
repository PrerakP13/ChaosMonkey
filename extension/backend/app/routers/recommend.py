from fastapi import APIRouter
from backend.app.services.analyzer import generate_recommendations

router = APIRouter(prefix="/recommend", tags=["Recommend"])

@router.post("/")
def recommend_endpoint(payload: dict):
    analysis = payload["analysis"]
    return generate_recommendations(analysis)
