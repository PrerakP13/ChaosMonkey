from fastapi import APIRouter
from backend.app.services.analyzer import analyze_project

router = APIRouter(prefix="/analyze", tags=["Analyze"])

@router.post("/")
def analyze_endpoint(payload: dict):
    services = payload["services"]
    dependencies = payload["dependencies"]

    analysis = analyze_project(services, dependencies)
    return analysis
