from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base
from app.models._types import TimestampTZ


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    plan: Mapped[str] = mapped_column(String(16), nullable=False)    # 'month', 'year', 'trial'
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # 'active', 'cancelled', 'expired', 'pending'

    started_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TimestampTZ, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(TimestampTZ)

    payment_provider: Mapped[str | None] = mapped_column(String(32))  # 'yukassa', 'tg_stars'
    payment_id: Mapped[str | None] = mapped_column(Text, unique=True)
    amount_rub: Mapped[float | None] = mapped_column(Numeric(8, 2))

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
