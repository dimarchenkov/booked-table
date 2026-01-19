from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Closure(Base):
    __tablename__ = "closures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    table_id: Mapped[int | None] = mapped_column(ForeignKey("tables.id"))
    reason: Mapped[str | None] = mapped_column(String(255))
