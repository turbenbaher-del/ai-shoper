from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base
from app.models._types import JsonB, TimestampTZ


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(Text)
    tg_first_name: Mapped[str | None] = mapped_column(Text)
    tg_language_code: Mapped[str] = mapped_column(String(8), default="ru")
    created_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(TimestampTZ, server_default=func.now())

    # Онбординг
    quiz_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_data: Mapped[dict | None] = mapped_column(JsonB)

    # Лимиты
    free_searches_used: Mapped[int] = mapped_column(Integer, default=0)
    free_searches_reset_at: Mapped[datetime | None] = mapped_column(TimestampTZ)

    # Premium
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[datetime | None] = mapped_column(TimestampTZ)
    premium_plan: Mapped[str | None] = mapped_column(String(16))

    # Согласия
    pdn_consent_at: Mapped[datetime | None] = mapped_column(TimestampTZ)
    push_consent: Mapped[bool] = mapped_column(Boolean, default=False)
