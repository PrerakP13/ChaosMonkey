from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.simulation import SimulationCreate, SimulationRead
from backend.app.services.simulation_service import run_simulation
from backend.app.models.simulation import Simulation

router = APIRouter(prefix="/simulations", tags=["Simulations"])


@router.post("", response_model=SimulationRead)
def simulate(payload: SimulationCreate, db: Session = Depends(get_db)):
    return run_simulation(db, payload.architecture_id, payload.failed_service_id)


@router.get("/{simulation_id}", response_model=SimulationRead)
def get_simulation(simulation_id: int, db: Session = Depends(get_db)):
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation