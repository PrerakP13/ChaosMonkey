from datetime import datetime
from typing import List

from pydantic import BaseModel

from .simulation_result import SimulationResultRead


class SimulationBase(BaseModel):
    architecture_id: int
    failed_service_id: int


class SimulationCreate(SimulationBase):
    pass


class SimulationRead(BaseModel):
    id: int
    architecture_id: int
    failed_service_id: int
    created_at: datetime
    results: List[SimulationResultRead] = []

    model_config = {"from_attributes": True}