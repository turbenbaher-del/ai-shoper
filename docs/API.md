# AI-шопер · HTTP API

**Base URL:** `/api/v1`  
**Auth:** `Authorization: Bearer <token>` (получается из `/auth/telegram`)

---

## Auth

### POST /auth/telegram
Авторизация по Telegram initData.

**Body:**
```json
{ "init_data": "query_id=...&user=...&hash=..." }
```

**Response:**
```json
{
  "user": { "id": 1, "tg_user_id": 123, "is_premium": false, "free_searches_used": 0 },
  "token": "abc123",
  "is_new": true
}
```

### POST /quiz
Сохранение результатов онбординга.

**Body:**
```json
{ "who": "для себя", "marketplaces": ["ozon"], "priority": "цена", "categories": ["электроника"] }
```

---

## Search

### POST /search
Основной поиск товаров.

**Body:** `{ "query": "робот-пылесос до 30к для кота" }`

**Response:**
```json
{
  "query_id": 42,
  "query": "робот-пылесос до 30к для кота",
  "title": "Нашёл 3 варианта",
  "subtitle": "Прочитал 187 отзывов · сравнил 3 маркетплейса · отсёк 12 накруток",
  "products": [...],
  "share_text": "...",
  "processing_time_seconds": 12.4,
  "needs_clarification": false
}
```

**402 при исчерпании лимита:**
```json
{ "detail": { "paywall": true, "message": "Исчерпан лимит" } }
```

### GET /search/history?limit=20
История запросов текущего пользователя.

### GET /search/{id}
Детали конкретного запроса.

### GET /search/{query_id}/{product_idx}/click
Редирект на маркетплейс с CPA-тегом + логирование клика.

---

## Tracked

### GET /tracked
Список отслеживаемых товаров.

### POST /tracked
Добавить товар в отслеживание.

**Body:**
```json
{
  "marketplace": "ozon",
  "sku": "123456",
  "name": "Пылесос Xiaomi",
  "url": "https://ozon.ru/...",
  "image_url": null,
  "initial_price": 15990
}
```

**402** если превышен лимит (3 товара для free).

### DELETE /tracked/{id}
Снять с отслеживания.

### GET /tracked/{id}/history
История цен для графика.

---

## Subscription

### GET /subscription
Статус подписки.

### POST /subscription/start
Начать подписку.

**Body:** `{ "plan": "month" | "year" | "trial" }`

**Response trial:** `{ "ok": true }`  
**Response paid:** `{ "redirect_url": "https://yookassa.ru/..." }`

### POST /subscription/cancel
Отменить подписку.

---

## Webhook

### POST /webhook/yukassa
Нотификации от ЮKassa. Только для ЮKassa, проверяется HMAC подпись.
