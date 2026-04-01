from pydantic import BaseModel


class DependencyBase(BaseModel):
    source_service_id: int
    target_service_id: int


class DependencyCreate(DependencyBase):
    pass


class DependencyRead(DependencyBase):
    id: int

    model_config = {"from_attributes": True}