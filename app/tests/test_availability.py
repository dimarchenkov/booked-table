from __future__ import annotations

from datetime import date

from app.models import Closure, ScheduleRule, Table, WorkingHour
from app.services.availability_service import generate_availability_slots


def test_availability_with_closure(session):
    table = Table(name="A1")
    session.add(table)
    session.commit()

    schedule = ScheduleRule(
        timezone="UTC",
        slot_minutes=60,
        buffer_minutes=0,
        min_booking_minutes=60,
        max_booking_minutes=240,
        hold_minutes=10,
    )
    session.add(schedule)
    session.add(
        WorkingHour(
            weekday=0,
            start_time="09:00",
            end_time="12:00",
            is_open=True,
        )
    )
    session.commit()

    test_date = date(2025, 1, 6)  # Monday
    slots = generate_availability_slots(session, table_id=table.id, date_value=test_date)
    assert len(slots) == 3

    session.add(Closure(date=test_date, table_id=None, reason="Holiday"))
    session.commit()
    slots_after = generate_availability_slots(session, table_id=table.id, date_value=test_date)
    assert slots_after == []
