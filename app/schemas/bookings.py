from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.booking import Booking, BookingStatus


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

    @classmethod
    def from_model(cls, booking: Booking) -> "BookingResponse":
        return cls(
            id=booking.id,
            table_id=booking.table_id,
            client_id=booking.client_id,
            start_at=booking.start_at,
            end_at=booking.end_at,
            status=booking.status,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            calendar_event_uid=booking.calendar_event_uid,
            calendar_event_href=booking.calendar_event_href,
        )


class BookingHoldResponse(BaseModel):
    booking_id: int = Field(..., alias="bookingId")
    payment_url: Optional[str] = Field(None, alias="paymentUrl")
