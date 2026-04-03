from app.db.database import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)

    source_service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_service = relationship(
        "Service",
        foreign_keys=[source_service_id],
        back_populates="outgoing_dependencies",
    )

    target_service = relationship(
        "Service",
        foreign_keys=[target_service_id],
        back_populates="incoming_dependencies",
    )