from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_shoper",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.price_tracker", "app.workers.alerts"],
)

celery_app.conf.beat_schedule = {
    # Раз в час — проверка цен tracked_items
    "check-prices-hourly": {
        "task": "app.workers.price_tracker.check_all_prices",
        "schedule": 3600.0,
    },
    # Раз в час — снятие премиума у пользователей с истёкшей подпиской
    "expire-premium-hourly": {
        "task": "app.workers.price_tracker.expire_premium",
        "schedule": 3600.0,
    },
    # Раз в сутки — чистка истёкших данных
    "cleanup-daily": {
        "task": "app.workers.price_tracker.cleanup_expired",
        "schedule": 86400.0,
    },
}
celery_app.conf.timezone = "UTC"
celery_app.conf.task_acks_late = True          # ACK только после успешного выполнения
celery_app.conf.worker_prefetch_multiplier = 1 # не забираем больше задач чем можем обработать
