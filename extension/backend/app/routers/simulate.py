from fastapi import APIRouter
from backend.app.services.failure_simulator import simulate_failures

router = APIRouter(prefix="/simulate", tags=["Simulate"])

@router.post("/random")
def simulate_endpoint(payload: dict):
    services = payload["services"]
    dependencies = payload["dependencies"]
    failed = payload["failed"]

    return simulate_failures(services, dependencies, failed)
