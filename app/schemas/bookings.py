from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.booking import BookingStatus


class BookingHoldRequest(BaseModel):
    table_id: int
    start_at: datetime
    end_at: datetime
    tg_user_id: int
    name: Optional[str] = None
    phone: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    table_id: int
    client_id: int
    start_at: datetime
    end_at: datetime
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    calendar_event_uid: Optional[str] = None
    calendar_event_href: Optional[str] = None


class BookingHoldResponse(BaseModel):
    booking_id: int = Field(..., alias="bookingId")
    payment_url: Optional[str] = Field(None, alias="paymentUrl")
