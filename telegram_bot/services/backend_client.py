from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from telegram_bot.settings import settings


class BackendClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_api_url.rstrip("/")

    async def get_tables(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/tables")
            response.raise_for_status()
            return response.json()

    async def get_availability(self, table_id: int, date_value: date) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/availability",
                params={"table_id": table_id, "date": date_value.isoformat()},
            )
            response.raise_for_status()
            return response.json()

    async def create_hold(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.base_url}/bookings/hold", json=payload)
            response.raise_for_status()
            return response.json()

    async def cancel_booking(self, booking_id: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.base_url}/bookings/{booking_id}/cancel")
            response.raise_for_status()
            return response.json()

    async def list_bookings(self, tg_user_id: int) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/clients/{tg_user_id}/bookings")
            response.raise_for_status()
            return response.json()
