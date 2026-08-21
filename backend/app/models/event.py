from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    vehicle_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    object_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    recommendation: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )