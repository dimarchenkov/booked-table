from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.services.integrations.payment import get_payment_provider
from app.workers.tasks import enqueue_calendar_create

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhooks/tbank")
async def tbank_webhook(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    if not settings.tbank_enabled:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="TBank disabled")

    payload = await request.json()
    safe_payload = {k: v for k, v in payload.items() if k.lower() not in {"token", "password"}}
    logger.info("TBank webhook received", extra={"payload": safe_payload})

    provider = get_payment_provider()
    if not provider.verify_webhook(payload):
        raise HTTPException(status_code=400, detail="Invalid token")

    payment_id = payload.get("PaymentId")
    if not payment_id:
        raise HTTPException(status_code=400, detail="Missing payment id")

    payment = session.scalar(select(Payment).where(Payment.provider_payment_id == str(payment_id)))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    new_status = provider.map_status(payload.get("Status", ""))
    if payment.status.value == new_status:
        return {"status": "ok"}

    payment.status = PaymentStatus(new_status)
    booking = session.scalar(select(Booking).where(Booking.id == payment.booking_id))
    if booking:
        if payment.status == PaymentStatus.PAID:
            booking.status = BookingStatus.CONFIRMED
            session.add(booking)
        elif payment.status in {PaymentStatus.FAILED, PaymentStatus.CANCELLED}:
            if booking.status == BookingStatus.HOLD:
                booking.status = BookingStatus.EXPIRED
                session.add(booking)
    session.add(payment)
    session.commit()

    if booking and booking.status == BookingStatus.CONFIRMED:
        enqueue_calendar_create.delay(booking.id)

    return {"status": "ok"}
