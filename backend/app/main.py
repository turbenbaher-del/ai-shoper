import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, search, subscription, tracked, webhook
from app.config import settings

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.env)

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


def _run_migrations() -> None:
    try:
        from alembic.config import Config
        from alembic import command
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations applied")
    except Exception as e:
        logger.error("Migration failed: %s", e)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()
    yield


app = FastAPI(
    title="AI-шопер API",
    version="1.0.0",
    docs_url="/docs" if settings.env != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(tracked.router, prefix=API_PREFIX)
app.include_router(subscription.router, prefix=API_PREFIX)
app.include_router(webhook.router, prefix=API_PREFIX)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Неверный формат запроса", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка. Попробуй позже."},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/v1/admin/setup-webhook")
async def setup_webhook(request: Request):
    """Регистрирует webhook бота. Вызывать один раз после деплоя."""
    secret = request.headers.get("X-Admin-Secret", "")
    if not secret or secret != settings.secret_key:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    body = await request.json()
    webhook_url = body.get("url")
    if not webhook_url:
        return JSONResponse(status_code=400, content={"detail": "url required"})

    from app.telegram.bot import set_webhook
    ok = await set_webhook(webhook_url)
    return {"ok": ok, "webhook_url": webhook_url}


@app.post("/api/v1/telegram/webhook")
async def telegram_webhook(request: Request):
    """Точка входа для webhook Telegram бота."""
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret != settings.telegram_webhook_secret:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    update = await request.json()
    from app.telegram.handlers import process_update
    await process_update(update)
    return {"ok": True}
