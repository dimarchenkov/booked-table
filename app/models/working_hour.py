from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkingHour(Base):
    __tablename__ = "working_hours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
