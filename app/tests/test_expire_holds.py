from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import Booking, BookingStatus, Client, Table
from app.workers.tasks import expire_holds


def test_expire_holds(session):
    table = Table(name="A1")
    client = Client(tg_user_id=2, name="Client")
    session.add_all([table, client])
    session.commit()

    booking = Booking(
        table_id=table.id,
        client_id=client.id,
        start_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        end_at=datetime.now(tz=timezone.utc) + timedelta(hours=2),
        status=BookingStatus.HOLD,
    )
    session.add(booking)
    session.commit()

    old_time = datetime.now(tz=timezone.utc) - timedelta(minutes=11)
    booking.created_at = old_time
    session.add(booking)
    session.commit()

    expired = expire_holds()
    session.refresh(booking)

    assert expired == 1
    assert booking.status == BookingStatus.EXPIRED
