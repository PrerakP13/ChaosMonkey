from pydantic import BaseModel


class SimulationResultRead(BaseModel):
    id: int
    simulation_id: int
    service_id: int
    status: str  # HEALTHY, FAILED, DEGRADED

    model_config = {"from_attributes": True}