from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.availability import SlotAvailability
from app.services.availability_service import generate_availability_slots

router = APIRouter()


@router.get("/availability", response_model=list[SlotAvailability])
def availability(
    table_id: int = Query(...),
    date_value: date = Query(..., alias="date"),
    session: Session = Depends(get_session),
) -> list[SlotAvailability]:
    slots = generate_availability_slots(session, table_id=table_id, date_value=date_value)
    return [SlotAvailability(**slot) for slot in slots]
