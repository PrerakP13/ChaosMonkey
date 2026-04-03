from datetime import datetime

from app.db.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship


class Architecture(Base):
    __tablename__ = "architectures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(225), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    services = relationship(
        "Service",
        back_populates="architecture",
        cascade="all, delete-orphan",
    )

    simulations = relationship(
        "Simulation",
        back_populates="architecture",
        cascade="all, delete-orphan",
    )