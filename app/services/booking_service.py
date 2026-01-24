from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Booking, BookingStatus, Client, ScheduleRule
from app.models.payment import Payment, PaymentStatus
from app.services.integrations.payment import get_payment_provider


class OverlapError(Exception):
    """Raised when an overlapping booking is attempted."""


class BookingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.payment_provider = get_payment_provider()

    def get_schedule(self) -> ScheduleRule:
        schedule = self.session.scalar(select(ScheduleRule))
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
        self.session.add(schedule)
        self.session.commit()
        return schedule

    def upsert_client(self, *, tg_user_id: int, name: str | None, phone: str | None) -> Client:
        client = self.session.scalar(select(Client).where(Client.tg_user_id == tg_user_id))
        if client:
            client.name = name or client.name
            client.phone = phone or client.phone
            return client
        client = Client(tg_user_id=tg_user_id, name=name, phone=phone)
        self.session.add(client)
        self.session.flush()
        return client

    def create_hold(
        self,
        *,
        table_id: int,
        start_at: datetime,
        end_at: datetime,
        tg_user_id: int,
        name: str | None,
        phone: str | None,
    ) -> tuple[Booking, Payment]:
        """Create a HOLD booking and related payment record in a transaction."""

        client = self.upsert_client(tg_user_id=tg_user_id, name=name, phone=phone)
        booking = Booking(
            table_id=table_id,
            client_id=client.id,
            start_at=start_at,
            end_at=end_at,
            status=BookingStatus.HOLD,
        )
        payment = Payment(
            booking_id=0,
            amount=settings.booking_price_rub,
            currency="RUB",
            status=PaymentStatus.NEW,
        )
        self.session.add(booking)
        self.session.flush()
        payment.booking_id = booking.id
        self.session.add(payment)
        self.session.flush()
        return booking, payment

    async def init_payment(self, booking: Booking, payment: Payment) -> dict:
        """Initialize payment with provider and update payment metadata."""

        data = await self.payment_provider.init_payment(
            order_id=f"booking-{booking.id}",
            amount=payment.amount,
            description=f"Booking #{booking.id}",
        )
        payment.payment_url = data.get("PaymentURL")
        payment.provider_payment_id = data.get("PaymentId")
        payment.status = PaymentStatus.PENDING if data.get("Success") else PaymentStatus.FAILED
        self.session.add(payment)
        self.session.commit()
        return data

    def confirm_booking(self, booking: Booking) -> Booking:
        """Confirm booking manually for MVP/manual testing."""

        booking.status = BookingStatus.CONFIRMED
        booking.updated_at = datetime.now(tz=timezone.utc)
        self.session.add(booking)
        self.session.commit()
        return booking

    def cancel_booking(self, booking: Booking) -> Booking:
        """Cancel booking by setting status to CANCELLED."""

        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.now(tz=timezone.utc)
        self.session.add(booking)
        self.session.commit()
        return booking


async def create_hold_with_payment(
    session: Session,
    *,
    table_id: int,
    start_at: datetime,
    end_at: datetime,
    tg_user_id: int,
    name: str | None,
    phone: str | None,
) -> tuple[Booking, Payment, dict]:
    """Create HOLD booking with payment and provider initialization.

    Relies on DB exclusion constraint to detect overlaps and raises OverlapError.
    """

    service = BookingService(session)
    try:
        booking, payment = service.create_hold(
            table_id=table_id,
            start_at=start_at,
            end_at=end_at,
            tg_user_id=tg_user_id,
            name=name,
            phone=phone,
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise OverlapError("Overlapping booking") from exc

    data = await service.init_payment(booking, payment)
    return booking, payment, data
