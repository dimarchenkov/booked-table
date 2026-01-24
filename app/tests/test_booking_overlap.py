from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Booking, BookingStatus, Client, Table


def test_booking_overlap(session):
    table = Table(name="A1")
    client = Client(tg_user_id=1, name="Test")
    session.add_all([table, client])
    session.commit()

    start = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    end = start + timedelta(hours=1)

    booking = Booking(
        table_id=table.id,
        client_id=client.id,
        start_at=start,
        end_at=end,
        status=BookingStatus.CONFIRMED,
    )
    session.add(booking)
    session.commit()

    overlapping = Booking(
        table_id=table.id,
        client_id=client.id,
        start_at=start + timedelta(minutes=30),
        end_at=end + timedelta(minutes=30),
        status=BookingStatus.HOLD,
    )
    session.add(overlapping)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
