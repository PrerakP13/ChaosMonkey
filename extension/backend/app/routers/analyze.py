from fastapi import APIRouter, Request
from app.services.analyzer import analyze_project
import json

router = APIRouter(prefix="/analyze", tags=["Analyze"])

@router.post("/")
async def analyze_endpoint(request: Request):
    print("[Backend] /analyze endpoint called")
    payload = await request.json()
    print(f"[Backend] Analyze payload: {json.dumps(payload, indent=2)[:200]}...")
    
    services = payload["services"]
    dependencies = payload["dependencies"]

    analysis = analyze_project(services, dependencies)
    print(f"[Backend] Analyze returning result")
    return analysis
