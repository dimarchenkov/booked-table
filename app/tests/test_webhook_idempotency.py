from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models import Booking, BookingStatus, Client, Payment, PaymentStatus, Table
from app.services.tbank import TBankClient


def test_webhook_idempotency(client, session):
    settings.tbank_password = "test-secret"
    tbank = TBankClient()

    table = Table(name="A1")
    client_model = Client(tg_user_id=3, name="Tester")
    session.add_all([table, client_model])
    session.commit()

    booking = Booking(
        table_id=table.id,
        client_id=client_model.id,
        start_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        end_at=datetime.now(tz=timezone.utc) + timedelta(hours=2),
        status=BookingStatus.HOLD,
    )
    session.add(booking)
    session.commit()

    payment = Payment(
        booking_id=booking.id,
        amount=1000,
        currency="RUB",
        status=PaymentStatus.PENDING,
        provider_payment_id="12345",
    )
    session.add(payment)
    session.commit()

    payload = {
        "TerminalKey": settings.tbank_terminal_key,
        "OrderId": f"booking-{booking.id}",
        "PaymentId": payment.provider_payment_id,
        "Status": "CONFIRMED",
        "Success": True,
        "Amount": payment.amount,
    }
    payload["Token"] = tbank._token(payload)

    response = client.post("/webhooks/tbank", json=payload)
    assert response.status_code == 200

    response = client.post("/webhooks/tbank", json=payload)
    assert response.status_code == 200

    session.refresh(payment)
    session.refresh(booking)
    assert payment.status == PaymentStatus.PAID
    assert booking.status == BookingStatus.CONFIRMED
