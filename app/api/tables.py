from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.table import Table
from app.schemas.tables import TableResponse

router = APIRouter()


@router.get("/tables", response_model=list[TableResponse])
def list_tables(session: Session = Depends(get_session)) -> list[TableResponse]:
    tables = session.scalars(select(Table).where(Table.active.is_(True))).all()
    return [
        TableResponse(id=table.id, name=table.name, location=table.location, active=table.active)
        for table in tables
    ]
