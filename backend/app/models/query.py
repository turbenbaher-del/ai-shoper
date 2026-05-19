from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base
from app.models._types import JsonB, TimestampTZ


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_request: Mapped[dict] = mapped_column(JsonB, nullable=False)

    products: Mapped[dict] = mapped_column(JsonB, nullable=False)
    total_cost_rub: Mapped[float | None] = mapped_column(Numeric(8, 2))
    processing_time_seconds: Mapped[float | None] = mapped_column(Numeric(5, 1))

    is_clarification: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_buy: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_share: Mapped[bool] = mapped_column(Boolean, default=False)
    cpa_tracking_id: Mapped[str | None] = mapped_column(Text)
