from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SlotAvailability(BaseModel):
    start_at: datetime
    end_at: datetime
    available: bool
