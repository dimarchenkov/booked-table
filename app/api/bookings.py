from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.booking import Booking, BookingStatus
from app.schemas.bookings import BookingHoldRequest, BookingHoldResponse, BookingResponse
from app.services.booking import OverlapError, create_hold_with_payment
from app.workers.tasks import enqueue_calendar_delete

router = APIRouter()


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
    return BookingResponse(
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


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(booking_id: int, session: Session = Depends(get_session)) -> BookingResponse:
    booking = session.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status in {BookingStatus.CANCELLED, BookingStatus.EXPIRED}:
        return BookingResponse(
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
    booking.status = BookingStatus.CANCELLED
    session.add(booking)
    session.commit()
    enqueue_calendar_delete.delay(booking.id)
    return BookingResponse(
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
