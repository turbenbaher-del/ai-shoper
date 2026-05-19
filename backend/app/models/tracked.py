from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base
from app.models._types import TimestampTZ


class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())

    marketplace: Mapped[str] = mapped_column(String(32), nullable=False)
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)

    initial_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())

    alert_threshold_pct: Mapped[int] = mapped_column(Integer, default=5)
    last_alert_sent_at: Mapped[datetime | None] = mapped_column(TimestampTZ)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tracked_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tracked_items.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())
