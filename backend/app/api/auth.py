import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from urllib.parse import parse_qsl, unquote

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models.user import User
from app.schemas.user import AuthRequest, AuthResponse, QuizData, UserOut
from app.api.deps import get_current_user, register_session

router = APIRouter(prefix="/auth", tags=["auth"])


def validate_telegram_init_data(init_data: str) -> dict:
    """Валидация initData по HMAC согласно документации Telegram."""
    parsed = dict(parse_qsl(unquote(init_data), keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("No hash in initData")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > 3600:
        raise ValueError("initData expired")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Invalid hash")

    return json.loads(parsed.get("user", "{}"))


def _make_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)


@router.post("/telegram", response_model=AuthResponse)
async def auth_telegram(body: AuthRequest, session: AsyncSession = Depends(get_session)):
    if settings.env == "development" and not settings.telegram_bot_token:
        tg_user = {"id": 123456789, "first_name": "Dev", "username": "devuser", "language_code": "ru"}
    else:
        try:
            tg_user = validate_telegram_init_data(body.init_data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tg_id = tg_user["id"]
    result = await session.execute(select(User).where(User.tg_user_id == tg_id))
    user = result.scalar_one_or_none()
    is_new = user is None

    if is_new:
        user = User(
            tg_user_id=tg_id,
            tg_username=tg_user.get("username"),
            tg_first_name=tg_user.get("first_name"),
            tg_language_code=tg_user.get("language_code", "ru"),
        )
        session.add(user)

    user.last_active_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(user)

    token = _make_token()
    register_session(token, user.id)  # регистрируем токен для авторизации

    return AuthResponse(user=UserOut.model_validate(user), token=token, is_new=is_new)


@router.post("/quiz")
async def save_quiz(
    body: QuizData,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user.quiz_data = body.model_dump()
    user.quiz_completed = True
    await session.commit()
    return {"ok": True}


@router.post("/consent")
async def save_pdn_consent(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Сохраняет согласие на обработку персональных данных."""
    user.pdn_consent_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True}
