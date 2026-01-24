from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Booking, BookingStatus, Closure, ScheduleRule, WorkingHour


def get_schedule(session: Session) -> ScheduleRule:
    schedule = session.scalar(select(ScheduleRule))
    if schedule:
        return schedule
    schedule = ScheduleRule(
        timezone=settings.timezone,
        slot_minutes=60,
        buffer_minutes=0,
        min_booking_minutes=60,
        max_booking_minutes=240,
        hold_minutes=10,
    )
    session.add(schedule)
    session.commit()
    return schedule


def is_closed(session: Session, *, table_id: int, date_value: date) -> bool:
    return (
        session.scalar(
            select(Closure.id).where(
                and_(
                    Closure.date == date_value,
                    (Closure.table_id.is_(None) | (Closure.table_id == table_id)),
                )
            )
        )
        is not None
    )


def generate_availability_slots(
    session: Session,
    *,
    table_id: int,
    date_value: date,
) -> list[dict]:
    """Generate availability slots based on schedule rules, working hours, closures, and bookings."""

    schedule = get_schedule(session)
    working_hours = session.scalar(
        select(WorkingHour).where(WorkingHour.weekday == date_value.weekday())
    )
    if not working_hours or not working_hours.is_open:
        return []
    if is_closed(session, table_id=table_id, date_value=date_value):
        return []

    tz = ZoneInfo(schedule.timezone)
    start_hour, start_minute = map(int, working_hours.start_time.split(":"))
    end_hour, end_minute = map(int, working_hours.end_time.split(":"))

    start_local = datetime.combine(date_value, time(start_hour, start_minute), tzinfo=tz)
    end_local = datetime.combine(date_value, time(end_hour, end_minute), tzinfo=tz)

    slot_minutes = schedule.slot_minutes
    buffer_minutes = schedule.buffer_minutes

    slots: list[dict] = []
    cursor = start_local
    while cursor + timedelta(minutes=slot_minutes) <= end_local:
        slot_start = cursor
        slot_end = cursor + timedelta(minutes=slot_minutes)
        check_start = slot_start - timedelta(minutes=buffer_minutes)
        check_end = slot_end + timedelta(minutes=buffer_minutes)

        overlapping = session.scalar(
            select(Booking.id).where(
                and_(
                    Booking.table_id == table_id,
                    Booking.status.in_([BookingStatus.HOLD, BookingStatus.CONFIRMED]),
                    Booking.start_at < check_end.astimezone(timezone.utc),
                    Booking.end_at > check_start.astimezone(timezone.utc),
                )
            )
        )
        slots.append(
            {
                "start_at": slot_start.astimezone(timezone.utc),
                "end_at": slot_end.astimezone(timezone.utc),
                "available": overlapping is None,
            }
        )
        cursor += timedelta(minutes=slot_minutes)
    return slots
