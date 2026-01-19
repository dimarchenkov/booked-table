from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


booking_status = postgresql.ENUM(
    "HOLD",
    "CONFIRMED",
    "CANCELLED",
    "EXPIRED",
    name="booking_status",
)

payment_status = postgresql.ENUM(
    "NEW",
    "PENDING",
    "PAID",
    "FAILED",
    "CANCELLED",
    name="payment_status",
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    booking_status.create(op.get_bind(), checkfirst=True)
    payment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("location", sa.String(length=255)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120)),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "schedule_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("slot_minutes", sa.Integer(), nullable=False),
        sa.Column("buffer_minutes", sa.Integer(), nullable=False),
        sa.Column("min_booking_minutes", sa.Integer(), nullable=False),
        sa.Column("max_booking_minutes", sa.Integer(), nullable=False),
    )

    op.create_table(
        "working_hours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("end_time", sa.String(length=5), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "closures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("table_id", sa.Integer(), sa.ForeignKey("tables.id")),
        sa.Column("reason", sa.String(length=255)),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_id", sa.Integer(), sa.ForeignKey("tables.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="HOLD"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("calendar_event_uid", sa.String(length=255)),
        sa.Column("calendar_event_href", sa.String(length=255)),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="tbank"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="RUB"),
        sa.Column("status", payment_status, nullable=False, server_default="NEW"),
        sa.Column("provider_payment_id", sa.String(length=120)),
        sa.Column("payment_url", sa.String(length=500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.execute(
        "ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap "
        "EXCLUDE USING gist (table_id WITH =, tsrange(start_at, end_at, '[]') WITH &&) "
        "WHERE (status IN ('HOLD', 'CONFIRMED'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_no_overlap")
    op.drop_table("payments")
    op.drop_table("bookings")
    op.drop_table("closures")
    op.drop_table("working_hours")
    op.drop_table("schedule_rules")
    op.drop_table("clients")
    op.drop_table("tables")
    payment_status.drop(op.get_bind(), checkfirst=True)
    booking_status.drop(op.get_bind(), checkfirst=True)
