from __future__ import annotations

from sqladmin import ModelView

from app.models import Booking, Closure, Payment, ScheduleRule, Table, WorkingHour


class TableAdmin(ModelView, model=Table):
    column_list = [Table.id, Table.name, Table.location, Table.active, Table.created_at]
    form_excluded_columns = [Table.created_at]
    can_delete = False


class ScheduleRuleAdmin(ModelView, model=ScheduleRule):
    column_list = [
        ScheduleRule.id,
        ScheduleRule.timezone,
        ScheduleRule.slot_minutes,
        ScheduleRule.buffer_minutes,
        ScheduleRule.min_booking_minutes,
        ScheduleRule.max_booking_minutes,
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
