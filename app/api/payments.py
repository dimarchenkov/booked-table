from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/payments/{order_id}/stub")
def stub_payment(order_id: str) -> dict:
    return {"status": "stub", "order_id": order_id}
