"""
Отдельный engine + session_maker для Celery воркеров.

FastAPI и Celery работают в разных процессах с разными event-loop'ами,
поэтому делим engine. Pool sizing подобран под рабочую нагрузку воркера
(BATCH_SIZE=100, CONCURRENCY=20 в price_tracker).
"""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

worker_engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=5,
    echo=False,
)

worker_session_maker = async_sessionmaker(worker_engine, expire_on_commit=False)
