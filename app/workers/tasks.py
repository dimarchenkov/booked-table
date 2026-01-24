from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Booking, BookingStatus, Table
from app.services.booking_service import BookingService
from app.services.integrations.calendar import get_calendar_provider
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def expire_holds() -> int:
    """Expire HOLD bookings older than configured hold_minutes."""

    expired_count = 0
    with SessionLocal() as session:
        hold_minutes = BookingService(session).get_schedule().hold_minutes
        cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=hold_minutes)
        bookings = session.scalars(
            select(Booking)
            .where(Booking.status == BookingStatus.HOLD)
            .where(Booking.created_at < cutoff)
        ).all()
        for booking in bookings:
            booking.status = BookingStatus.EXPIRED
            expired_count += 1
        session.commit()
        for booking in bookings:
            if booking.calendar_event_href or booking.calendar_event_uid:
                enqueue_calendar_delete.delay(booking.id)
    return expired_count


@celery_app.task
def enqueue_calendar_create(booking_id: int) -> None:
    sync_calendar_event.delay(booking_id, "create")


@celery_app.task
def enqueue_calendar_delete(booking_id: int) -> None:
    sync_calendar_event.delay(booking_id, "delete")


@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def sync_calendar_event(self, booking_id: int, action: str) -> None:
    """Sync booking event to calendar provider with retries."""

    try:
        with SessionLocal() as session:
            booking = session.scalar(select(Booking).where(Booking.id == booking_id))
            if not booking:
                return
            table = session.scalar(select(Table).where(Table.id == booking.table_id))
            if not table:
                return
            provider = get_calendar_provider()
            if action == "create":
                uid, href = provider.create_event(
                    table_id=table.id,
                    booking_id=booking.id,
                    start_at=booking.start_at,
                    end_at=booking.end_at,
                    table_name=table.name,
                )
                booking.calendar_event_uid = uid
                booking.calendar_event_href = href
            elif action == "delete":
                provider.delete_event(
                    table_id=table.id,
                    href=booking.calendar_event_href,
                    uid=booking.calendar_event_uid,
                )
                booking.calendar_event_uid = None
                booking.calendar_event_href = None
            session.add(booking)
            session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Calendar sync failed")
        raise self.retry(exc=exc)
