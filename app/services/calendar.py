from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

import caldav

from app.core.config import settings

logger = logging.getLogger(__name__)


class CalendarService:
    def __init__(self) -> None:
        self.client = caldav.DAVClient(
            url=settings.yandex_calendar_url,
            username=settings.yandex_login,
            password=settings.yandex_app_password,
        )
        self._calendar_mapping = self._load_calendar_mapping()

    def _load_calendar_mapping(self) -> dict[int, str]:
        if not settings.yandex_calendar_mapping:
            return {}
        try:
            data = json.loads(settings.yandex_calendar_mapping)
            return {int(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            logger.warning("Invalid Yandex calendar mapping")
            return {}

    def _get_calendar(self, table_id: int) -> caldav.Calendar:
        principal = self.client.principal()
        if table_id in self._calendar_mapping:
            return caldav.Calendar(client=self.client, url=self._calendar_mapping[table_id])
        calendars = principal.calendars()
        if not calendars:
            raise RuntimeError("No calendars available")
        return calendars[0]

    def create_event(
        self,
        *,
        table_id: int,
        booking_id: int,
        start_at: datetime,
        end_at: datetime,
        table_name: str,
    ) -> tuple[str, str]:
        calendar = self._get_calendar(table_id)
        uid = f"booking-{booking_id}"
        summary = f"Booking #{booking_id} - Table {table_name}"
        event = (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "BEGIN:VEVENT\n"
            f"UID:{uid}\n"
            f"DTSTART:{start_at.strftime('%Y%m%dT%H%M%SZ')}\n"
            f"DTEND:{end_at.strftime('%Y%m%dT%H%M%SZ')}\n"
            f"SUMMARY:{summary}\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        created = calendar.add_event(event)
        href = created.url
        return uid, href

    def delete_event(self, *, table_id: int, href: Optional[str], uid: Optional[str]) -> None:
        calendar = self._get_calendar(table_id)
        if href:
            event = calendar.event_by_url(href)
            event.delete()
            return
        if uid:
            events = calendar.search(uid=uid)
            for event in events:
                event.delete()
