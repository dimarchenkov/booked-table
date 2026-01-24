from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.schemas.bookings import BookingHoldRequest, BookingHoldResponse, BookingResponse
from app.services.booking_service import OverlapError, create_hold_with_payment, BookingService
from app.workers.tasks import enqueue_calendar_delete, enqueue_calendar_create

router = APIRouter()


def _require_admin_api_key(x_admin_api_key: str | None) -> None:
    if settings.debug:
        return
    if not x_admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin API key required")


@router.post("/bookings/hold", response_model=BookingHoldResponse)
async def hold_booking(
    payload: BookingHoldRequest, session: Session = Depends(get_session)
) -> BookingHoldResponse:
    try:
        booking, payment, _ = await create_hold_with_payment(
            session,
            table_id=payload.table_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
            tg_user_id=payload.tg_user_id,
            name=payload.name,
            phone=payload.phone,
        )
    except OverlapError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return BookingHoldResponse(bookingId=booking.id, paymentUrl=payment.payment_url)


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, session: Session = Depends(get_session)) -> BookingResponse:
    booking = session.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingResponse.from_model(booking)


@router.get("/clients/{tg_user_id}/bookings", response_model=list[BookingResponse])
def list_client_bookings(tg_user_id: int, session: Session = Depends(get_session)) -> list[BookingResponse]:
    client = session.scalar(select(Client).where(Client.tg_user_id == tg_user_id))
    if not client:
        return []
    bookings = session.scalars(
        select(Booking).where(
            Booking.client_id == client.id,
            Booking.status.in_([BookingStatus.HOLD, BookingStatus.CONFIRMED]),
        )
    ).all()
    return [BookingResponse.from_model(booking) for booking in bookings]


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(booking_id: int, session: Session = Depends(get_session)) -> BookingResponse:
    booking = session.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status in {BookingStatus.CANCELLED, BookingStatus.EXPIRED}:
        return BookingResponse.from_model(booking)
    service = BookingService(session)
    booking = service.cancel_booking(booking)
    enqueue_calendar_delete.delay(booking.id)
    return BookingResponse.from_model(booking)


@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking(
    booking_id: int,
    session: Session = Depends(get_session),
    x_admin_api_key: str | None = Header(default=None),
) -> BookingResponse:
    _require_admin_api_key(x_admin_api_key)
    booking = session.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    service = BookingService(session)
    booking = service.confirm_booking(booking)
    enqueue_calendar_create.delay(booking.id)
    return BookingResponse.from_model(booking)
