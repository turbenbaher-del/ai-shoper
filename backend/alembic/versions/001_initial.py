"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

# Кросс-диалектные типы
TZ = sa.DateTime(timezone=True)
JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("tg_username", sa.Text(), nullable=True),
        sa.Column("tg_first_name", sa.Text(), nullable=True),
        sa.Column("tg_language_code", sa.String(8), nullable=False, server_default="ru"),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("last_active_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("quiz_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiz_data", JSON_TYPE, nullable=True),
        sa.Column("free_searches_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("free_searches_reset_at", TZ, nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("premium_until", TZ, nullable=True),
        sa.Column("premium_plan", sa.String(16), nullable=True),
        sa.Column("pdn_consent_at", TZ, nullable=True),
        sa.Column("push_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tg_user_id"),
    )

    op.create_table(
        "queries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_request", JSON_TYPE, nullable=False),
        sa.Column("products", JSON_TYPE, nullable=False),
        sa.Column("total_cost_rub", sa.Numeric(8, 2), nullable=True),
        sa.Column("processing_time_seconds", sa.Numeric(5, 1), nullable=True),
        sa.Column("is_clarification", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("clicked_buy", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("clicked_share", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cpa_tracking_id", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_queries_user_id_created", "queries", ["user_id", sa.text("created_at DESC")])

    op.create_table(
        "tracked_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("marketplace", sa.String(32), nullable=False),
        sa.Column("sku", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("initial_price", sa.Integer(), nullable=False),
        sa.Column("current_price", sa.Integer(), nullable=False),
        sa.Column("last_checked_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("alert_threshold_pct", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_alert_sent_at", TZ, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tracked_user_active", "tracked_items", ["user_id", "is_active"])
    op.create_index(
        "idx_tracked_check",
        "tracked_items",
        ["last_checked_at"],
        postgresql_where=sa.text("is_active = TRUE"),
    )

    op.create_table(
        "price_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tracked_item_id", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("captured_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tracked_item_id"], ["tracked_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_price_history_item", "price_history", ["tracked_item_id", "captured_at"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("plan", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", TZ, nullable=False),
        sa.Column("cancelled_at", TZ, nullable=True),
        sa.Column("payment_provider", sa.String(32), nullable=True),
        sa.Column("payment_id", sa.Text(), nullable=True),
        sa.Column("amount_rub", sa.Numeric(8, 2), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id", name="uq_subscriptions_payment_id"),
    )
    op.create_index("idx_subs_user", "subscriptions", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("price_history")
    op.drop_table("tracked_items")
    op.drop_table("queries")
    op.drop_table("users")
