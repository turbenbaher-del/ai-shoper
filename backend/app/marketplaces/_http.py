"""
Shared HTTP-клиент для маркетплейсов: rate-limiting на каждый хост,
ретраи с экспоненциальным backoff, нормальный User-Agent.

Зачем не httpx-retries:
- Маркетплейсам нужен per-host limiter (10 req/sec на WB, 5 — на Ozon).
- Нужна async-безопасная семафора на конкурентность.
- Ретраить надо только определённые коды (429, 5xx, network), а не всё подряд.
"""
import asyncio
import logging
import random
import time
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Retryable status codes
_RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


@dataclass
class HostLimit:
    """Лимит на один хост: concurrency + минимальный интервал между запросами."""
    concurrency: int = 5
    min_interval_s: float = 0.1  # 10 req/sec по умолчанию

    semaphore: asyncio.Semaphore = field(init=False)
    last_request_at: float = field(default=0.0, init=False)
    _interval_lock: asyncio.Lock = field(init=False)

    def __post_init__(self) -> None:
        self.semaphore = asyncio.Semaphore(self.concurrency)
        self._interval_lock = asyncio.Lock()

    async def acquire(self) -> None:
        await self.semaphore.acquire()
        async with self._interval_lock:
            now = time.monotonic()
            wait = self.last_request_at + self.min_interval_s - now
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_request_at = time.monotonic()

    def release(self) -> None:
        self.semaphore.release()


# Конфигурация лимитов на каждый маркетплейс. Подбирается эмпирически.
_HOST_LIMITS: dict[str, HostLimit] = {
    "search.wb.ru": HostLimit(concurrency=4, min_interval_s=0.15),
    "card.wb.ru": HostLimit(concurrency=4, min_interval_s=0.15),
    "feedbacks1.wb.ru": HostLimit(concurrency=2, min_interval_s=0.3),
    "feedbacks2.wb.ru": HostLimit(concurrency=2, min_interval_s=0.3),
    "www.ozon.ru": HostLimit(concurrency=2, min_interval_s=0.3),
    "api-seller.ozon.ru": HostLimit(concurrency=3, min_interval_s=0.2),
    "api.partner.market.yandex.ru": HostLimit(concurrency=3, min_interval_s=0.25),
    "api.telegram.org": HostLimit(concurrency=10, min_interval_s=0.05),
}


def _limit_for(host: str) -> HostLimit:
    return _HOST_LIMITS.setdefault(host, HostLimit())


class MarketplaceClient:
    """
    Async HTTP-клиент с per-host rate-limiting + ретраи.
    Использовать как async context manager.
    """

    def __init__(self, timeout: float = 12.0, max_retries: int = 3, ua: str = DEFAULT_UA):
        self.timeout = timeout
        self.max_retries = max_retries
        self.ua = ua
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "MarketplaceClient":
        from app.config import settings  # lazy import to avoid circular

        client_kwargs: dict = {
            "timeout": self.timeout,
            "headers": {"User-Agent": self.ua, "Accept": "application/json,text/plain,*/*"},
            "follow_redirects": True,
        }
        if settings.marketplace_proxy_url:
            client_kwargs["proxy"] = settings.marketplace_proxy_url
            logger.debug("Using proxy: %s", settings.marketplace_proxy_url[:30])
        try:
            client_kwargs["http2"] = True
            self._client = httpx.AsyncClient(**client_kwargs)
        except Exception:
            # h2 package not installed — fall back to HTTP/1.1
            client_kwargs.pop("http2", None)
            self._client = httpx.AsyncClient(**client_kwargs)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        retry_on_4xx: bool = False,
    ) -> httpx.Response | None:
        """
        Возвращает Response при успехе, None при окончательной неудаче.
        Логирует ошибки, но не пробрасывает их — вызывающий должен сам решить
        как реагировать на отсутствие данных от одного маркетплейса.
        """
        assert self._client is not None, "Use async with MarketplaceClient()"
        host = httpx.URL(url).host
        limit = _limit_for(host)

        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            await limit.acquire()
            try:
                resp = await self._client.request(
                    method, url, params=params, json=json_body, headers=headers,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_err = e
                logger.warning("HTTP %s %s attempt %d: %s", method, url, attempt + 1, e)
            else:
                if resp.status_code < 400:
                    return resp
                if resp.status_code in _RETRYABLE_STATUS or (retry_on_4xx and resp.status_code >= 400):
                    last_err = httpx.HTTPStatusError(
                        f"{resp.status_code}", request=resp.request, response=resp
                    )
                    logger.warning(
                        "HTTP %s %s attempt %d → %d", method, url, attempt + 1, resp.status_code,
                    )
                else:
                    # Невосстановимая ошибка (404, 403 и т.п.) — не ретраим
                    logger.info("HTTP %s %s → %d (not retryable)", method, url, resp.status_code)
                    return None
            finally:
                limit.release()

            if attempt < self.max_retries:
                # Exponential backoff с джиттером
                delay = (2 ** attempt) * 0.5 + random.uniform(0, 0.3)
                await asyncio.sleep(delay)

        logger.error("HTTP %s %s failed after %d attempts: %s", method, url, self.max_retries + 1, last_err)
        return None

    async def get_json(self, url: str, **kwargs) -> dict | list | None:
        resp = await self.request("GET", url, **kwargs)
        if resp is None:
            return None
        ct = resp.headers.get("content-type", "")
        if "html" in ct:
            logger.warning("Non-JSON response (HTML) from %s — bot detection?", url)
            return None
        try:
            return resp.json()
        except Exception as e:
            logger.warning("Failed to parse JSON from %s: %s", url, e)
            return None

    async def post_json(self, url: str, body: dict, **kwargs) -> dict | list | None:
        resp = await self.request("POST", url, json_body=body, **kwargs)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception:
            return None
