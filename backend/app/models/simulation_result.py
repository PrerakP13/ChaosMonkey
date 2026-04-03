from app.db.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)

    simulation_id = Column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(String(225), nullable=False)  # HEALTHY, FAILED, DEGRADED

    simulation = relationship("Simulation", back_populates="results")
    service = relationship("Service", back_populates="simulation_results")