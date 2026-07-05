from fastapi import APIRouter, Request
from app.services.failure_simulator import simulate_failures
import json

router = APIRouter(prefix="/simulate", tags=["Simulate"])

@router.post("/random")
async def simulate_endpoint(request: Request):
    print("[Backend] /simulate/random endpoint called")
    payload = await request.json()
    print(f"[Backend] Payload received:")
    print(f"  - services: {len(payload.get('services', []))} items")
    print(f"  - First 3 services: {payload.get('services', [])[:3]}")
    print(f"  - dependencies: {len(payload.get('dependencies', []))} items")
    print(f"  - failed: {payload.get('failed', [])}")
    
    services = payload["services"]
    dependencies = payload["dependencies"]
    failed = payload["failed"]
    
    print(f"[Backend] Calling simulate_failures with {len(services)} services, {len(dependencies)} deps, {len(failed)} failed")
    result = simulate_failures(services, dependencies, failed)
    print(f"[Backend] simulate_failures returned: failed={len(result.get('failed', []))}, effects={len(result.get('effects', []))}, chains={len(result.get('chains', []))}")
    
    return result
