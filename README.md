# AI-шопер

Telegram Mini App для поиска лучших товаров на маркетплейсах (Ozon, Wildberries, Я.Маркет).

## Быстрый старт

```bash
# 1. Скопируй .env
cp backend/.env.example backend/.env
# Заполни ANTHROPIC_API_KEY и TELEGRAM_BOT_TOKEN

# 2. Поднять всё
docker-compose up

# 3. Применить миграции (в новом терминале)
docker-compose exec backend alembic upgrade head

# 4. Фронт открыт на http://localhost:5173
```

## Стек

- **Backend:** Python 3.11 + FastAPI + PostgreSQL + Redis + Celery
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **AI:** Anthropic Claude (Sonnet 4.6 + Opus 4.7)
- **Bot:** Telegram Bot API (через HTTP)
- **Payments:** ЮKassa

## Модели Claude

Согласно разделу 7.2 ТЗ:
- **Sonnet (`claude-sonnet-4-6`)** — парсинг запроса, фильтрация, форматирование результатов
- **Opus (`claude-opus-4-7`)** — анализ отзывов, ранжирование, дебаг сложных багов

## Структура

```
ai-shoper/
├── backend/         FastAPI приложение
├── frontend/        React Mini App
├── docs/            ТЗ, DECISIONS, API
└── docker-compose.yml
```

## Документы

- [ТЗ](ai_shoper_TZ.md)
- [Архитектурные решения](docs/DECISIONS.md)
- [API Reference](docs/API.md)

## Задачи по неделям

| Неделя | Фокус |
|--------|-------|
| 1 | Фундамент: FastAPI, БД, бот, пайплайн |
| 2 | Mini App каркас: компоненты, Welcome, Quiz, Home |
| 3 | Поиск: Input → Processing → Results |
| 4 | Tracked items + Paywall + ЮKassa |
| 5 | Реальные API маркетплейсов |
| 6 | Polish + деплой + soft launch |
