from __future__ import annotations

from datetime import datetime, timezone

from sqladmin import BaseView, ModelView, expose
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Booking, Closure, Payment, ScheduleRule, Table, WorkingHour
from app.models.booking import BookingStatus


class TableAdmin(ModelView, model=Table):
    column_list = [Table.id, Table.name, Table.location, Table.active, Table.created_at]
    form_excluded_columns = [Table.created_at]

    async def delete_model(self, request, pk):
        """Deactivate tables with future confirmed bookings instead of deleting."""

        with SessionLocal() as session:
            table = session.get(Table, pk)
            if not table:
                return False
            has_future_confirmed = session.scalar(
                select(Booking.id).where(
                    Booking.table_id == table.id,
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.start_at > datetime.now(tz=timezone.utc),
                )
            )
            if has_future_confirmed:
                table.active = False
                session.add(table)
                session.commit()
                return False
        return await super().delete_model(request, pk)


class ScheduleRuleAdmin(ModelView, model=ScheduleRule):
    column_list = [
        ScheduleRule.id,
        ScheduleRule.timezone,
        ScheduleRule.slot_minutes,
        ScheduleRule.buffer_minutes,
        ScheduleRule.min_booking_minutes,
        ScheduleRule.max_booking_minutes,
        ScheduleRule.hold_minutes,
    ]


class WorkingHourAdmin(ModelView, model=WorkingHour):
    column_list = [WorkingHour.weekday, WorkingHour.start_time, WorkingHour.end_time, WorkingHour.is_open]


class ClosureAdmin(ModelView, model=Closure):
    column_list = [Closure.date, Closure.table_id, Closure.reason]


class BookingAdmin(ModelView, model=Booking):
    column_list = [
        Booking.id,
        Booking.table_id,
        Booking.client_id,
        Booking.start_at,
        Booking.end_at,
        Booking.status,
        Booking.created_at,
        Booking.updated_at,
    ]
    can_create = False
    can_delete = False


class PaymentAdmin(ModelView, model=Payment):
    column_list = [
        Payment.id,
        Payment.booking_id,
        Payment.amount,
        Payment.currency,
        Payment.status,
        Payment.provider_payment_id,
        Payment.payment_url,
        Payment.created_at,
        Payment.updated_at,
    ]
    can_create = False
    can_delete = False


class GroupPosterView(BaseView):
    name = "Group Poster"
    icon = "fa fa-bullhorn"

    def _build_poster(self) -> tuple[str, str, str | None]:
        """Generate text and link for Telegram group poster."""

        bot_username = settings.telegram_bot_username or "<bot_username>"
        poster_text = (
            "📦 Аренда столов для упаковки. Нажмите кнопку ниже, чтобы забронировать время."
        )
        link = f"https://t.me/{bot_username}?start=from_group"
        instructions = None
        if bot_username == "<bot_username>":
            instructions = "Set TELEGRAM_BOT_USERNAME in .env or provide TELEGRAM_BOT_TOKEN to auto-detect."
        return poster_text, link, instructions

    @expose("/admin/group-poster")
    async def poster(self, request):
        poster_text, link, instructions = self._build_poster()
        return await self.render(
            request,
            "admin/group_poster.html",
            context={"poster_text": poster_text, "link": link, "instructions": instructions},
        )
