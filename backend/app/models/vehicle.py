from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    vehicle_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="offline"
    )

    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )