from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin

from app.admin.auth import AdminAuth
from app.admin.views import (
    BookingAdmin,
    ClosureAdmin,
    PaymentAdmin,
    ScheduleRuleAdmin,
    TableAdmin,
    WorkingHourAdmin,
)
from app.api.availability import router as availability_router
from app.api.bookings import router as bookings_router
from app.api.health import router as health_router
from app.api.tables import router as tables_router
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=settings.session_https_only,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tables_router)
app.include_router(availability_router)
app.include_router(bookings_router)
app.include_router(webhooks_router)

admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key=settings.secret_key))
admin.add_view(TableAdmin)
admin.add_view(ScheduleRuleAdmin)
admin.add_view(WorkingHourAdmin)
admin.add_view(ClosureAdmin)
admin.add_view(BookingAdmin)
admin.add_view(PaymentAdmin)
