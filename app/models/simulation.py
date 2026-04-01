from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)

    architecture_id = Column(
        Integer,
        ForeignKey("architectures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    failed_service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    architecture = relationship("Architecture", back_populates="simulations")
    failed_service = relationship("Service")

    results = relationship(
        "SimulationResult",
        back_populates="simulation",
        cascade="all, delete-orphan",
    )