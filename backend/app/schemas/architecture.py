from datetime import datetime
from pydantic import BaseModel


class ArchitectureBase(BaseModel):
    name: str


class ArchitectureCreate(ArchitectureBase):
    pass


class ArchitectureRead(ArchitectureBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}