from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    architecture_id = Column(
        Integer,
        ForeignKey("architectures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # API, DATABASE, CACHE, QUEUE, LOAD_BALANCER
    replica_group_id = Column(Integer, nullable=True)

    architecture = relationship("Architecture", back_populates="services")

    outgoing_dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.source_service_id",
        back_populates="source_service",
        cascade="all, delete-orphan",
    )

    incoming_dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.target_service_id",
        back_populates="target_service",
        cascade="all, delete-orphan",
    )

    simulation_results = relationship(
        "SimulationResult",
        back_populates="service",
        cascade="all, delete-orphan",
    )