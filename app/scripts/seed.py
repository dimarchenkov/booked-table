from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ScheduleRule, Table, WorkingHour


def seed() -> None:
    """Seed default schedule rules, working hours, and tables."""

    with SessionLocal() as session:
        schedule = session.scalar(select(ScheduleRule))
        if not schedule:
            schedule = ScheduleRule(
                timezone="Europe/Oslo",
                slot_minutes=60,
                buffer_minutes=0,
                min_booking_minutes=60,
                max_booking_minutes=240,
                hold_minutes=10,
            )
            session.add(schedule)

        existing_hours = session.scalars(select(WorkingHour)).all()
        if not existing_hours:
            for weekday in range(7):
                session.add(
                    WorkingHour(
                        weekday=weekday,
                        start_time="09:00",
                        end_time="21:00",
                        is_open=True,
                    )
                )

        existing_tables = session.scalars(select(Table)).all()
        if not existing_tables:
            session.add_all(
                [
                    Table(name="Table 1", location="Hall"),
                    Table(name="Table 2", location="Hall"),
                    Table(name="Table 3", location="Hall"),
                ]
            )

        session.commit()


if __name__ == "__main__":
    seed()
