from __future__ import annotations

from pydantic import BaseModel


class TableResponse(BaseModel):
    id: int
    name: str
    location: str | None
    active: bool
