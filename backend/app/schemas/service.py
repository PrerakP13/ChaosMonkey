from pydantic import BaseModel
from typing import Optional


class ServiceBase(BaseModel):
    architecture_id: int
    name: str
    type: str
    replica_group_id: Optional[int] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceRead(ServiceBase):
    id: int

    model_config = {"from_attributes": True}