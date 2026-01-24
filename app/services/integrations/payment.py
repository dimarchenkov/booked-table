from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentProvider(ABC):
    @abstractmethod
    async def init_payment(self, *, order_id: str, amount: int, description: str) -> dict[str, Any]:
        """Initialize a payment and return provider response metadata."""

    @abstractmethod
    def verify_webhook(self, payload: dict[str, Any]) -> bool:
        """Validate webhook payload signature."""

    @abstractmethod
    def map_status(self, status: str) -> str:
        """Map provider status string to internal payment status."""


class StubPaymentProvider(PaymentProvider):
    """Stub provider that returns a local payment URL without external calls."""

    async def init_payment(self, *, order_id: str, amount: int, description: str) -> dict[str, Any]:
        return {
            "Success": True,
            "PaymentId": f"stub-{order_id}",
            "PaymentURL": f"http://localhost:8000/payments/{order_id}/stub",
        }

    def verify_webhook(self, payload: dict[str, Any]) -> bool:
        return True

    def map_status(self, status: str) -> str:
        return "PAID" if status == "CONFIRMED" else "PENDING"


class TBankPaymentProvider(PaymentProvider):
    def __init__(self) -> None:
        self.base_url = "https://securepay.tinkoff.ru/v2"
        self.terminal_key = settings.tbank_terminal_key
        self.password = settings.tbank_password

    def _token(self, data: dict[str, Any]) -> str:
        fields = {k: v for k, v in data.items() if v is not None and k != "Token"}
        fields["Password"] = self.password
        token_string = "".join(str(fields[key]) for key in sorted(fields))
        return hashlib.sha256(token_string.encode("utf-8")).hexdigest()

    async def init_payment(self, *, order_id: str, amount: int, description: str) -> dict[str, Any]:
        payload = {
            "TerminalKey": self.terminal_key,
            "Amount": amount,
            "OrderId": order_id,
            "Description": description,
            "NotificationURL": settings.tbank_notification_url,
            "SuccessURL": settings.tbank_success_url,
            "FailURL": settings.tbank_fail_url,
            "RedirectDueDate": settings.tbank_redirect_due_minutes,
        }
        payload["Token"] = self._token(payload)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.base_url}/Init", json=payload)
            response.raise_for_status()
            data = response.json()
        if not data.get("Success"):
            logger.error("TBank Init failed", extra={"details": data.get("Message")})
        return data

    def verify_webhook(self, payload: dict[str, Any]) -> bool:
        if "Token" not in payload:
            return False
        expected = self._token(payload)
        return expected == payload.get("Token")

    def map_status(self, status: str) -> str:
        status_map = {
            "NEW": "PENDING",
            "FORM_SHOWED": "PENDING",
            "AUTHORIZED": "PAID",
            "CONFIRMED": "PAID",
            "REJECTED": "FAILED",
            "CANCELED": "CANCELLED",
            "DEADLINE_EXPIRED": "FAILED",
            "REFUNDED": "CANCELLED",
        }
        return status_map.get(status, "PENDING")


def get_payment_provider() -> PaymentProvider:
    """Return payment provider implementation based on settings."""

    if settings.tbank_enabled:
        return TBankPaymentProvider()
    return StubPaymentProvider()
