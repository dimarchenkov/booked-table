from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable

import pytz
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Booking, BookingStatus, Client, Closure, ScheduleRule, Table, WorkingHour
from app.models.payment import Payment
from app.models.payment import PaymentStatus
from app.services.tbank import TBankClient


class BookingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.tbank = TBankClient()

    def _get_schedule(self) -> ScheduleRule:
        schedule = self.session.scalar(select(ScheduleRule))
        if schedule:
            return schedule
        schedule = ScheduleRule(
            timezone=settings.timezone,
            slot_minutes=60,
            buffer_minutes=0,
            min_booking_minutes=60,
            max_booking_minutes=240,
        )
        self.session.add(schedule)
        self.session.commit()
        return schedule

    def _get_working_hours(self, weekday: int) -> WorkingHour | None:
        return self.session.scalar(select(WorkingHour).where(WorkingHour.weekday == weekday))

    def _is_closed(self, table_id: int, date_value: date) -> bool:
        closure = self.session.scalar(
            select(Closure).where(
                and_(
                    Closure.date == date_value,
                    (Closure.table_id.is_(None) | (Closure.table_id == table_id)),
                )
            )
        )
        return closure is not None

    def availability(self, *, table_id: int, date_value: date) -> list[dict]:
        schedule = self._get_schedule()
        tz = pytz.timezone(schedule.timezone)
        working_hours = self._get_working_hours(date_value.weekday())
        if not working_hours or not working_hours.is_open:
            return []
        if self._is_closed(table_id, date_value):
            return []

        start_hour, start_minute = map(int, working_hours.start_time.split(":"))
        end_hour, end_minute = map(int, working_hours.end_time.split(":"))
        start_local = tz.localize(datetime.combine(date_value, time(start_hour, start_minute)))
        end_local = tz.localize(datetime.combine(date_value, time(end_hour, end_minute)))

        slot_minutes = schedule.slot_minutes
        buffer_minutes = schedule.buffer_minutes

        slots = []
        cursor = start_local
        while cursor + timedelta(minutes=slot_minutes) <= end_local:
            slot_start = cursor
            slot_end = cursor + timedelta(minutes=slot_minutes)
            check_start = slot_start - timedelta(minutes=buffer_minutes)
            check_end = slot_end + timedelta(minutes=buffer_minutes)
            overlapping = self.session.scalar(
                select(Booking.id).where(
                    and_(
                        Booking.table_id == table_id,
                        Booking.status.in_([BookingStatus.HOLD, BookingStatus.CONFIRMED]),
                        Booking.start_at < check_end.astimezone(pytz.UTC),
                        Booking.end_at > check_start.astimezone(pytz.UTC),
                    )
                )
            )
            slots.append(
                {
                    "start_at": slot_start.astimezone(pytz.UTC),
                    "end_at": slot_end.astimezone(pytz.UTC),
                    "available": overlapping is None,
                }
            )
            cursor += timedelta(minutes=slot_minutes)
        return slots

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
    ) -> tuple[Booking, Payment, dict]:
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

        order_id = f"booking-{booking.id}"
        description = f"Booking #{booking.id}"
        return booking, payment, {"order_id": order_id, "description": description}

    async def finalize_payment(self, payment: Payment, booking: Booking) -> dict:
        data = await self.tbank.init_payment(
            order_id=f"booking-{booking.id}",
            amount=payment.amount,
            description=f"Booking #{booking.id}",
        )
        return data


class OverlapError(Exception):
    pass


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
    service = BookingService(session)
    try:
        booking, payment, meta = service.create_hold(
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

    data = await service.finalize_payment(payment, booking)
    payment.payment_url = data.get("PaymentURL")
    payment.provider_payment_id = data.get("PaymentId")
    payment.status = PaymentStatus.PENDING if data.get("Success") else PaymentStatus.FAILED
    session.add(payment)
    session.commit()
    return booking, payment, data
