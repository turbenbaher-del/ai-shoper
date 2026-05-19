from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""  # прокси для РФ, например vsegpt.ru

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_shoper"
    redis_url: str = "redis://localhost:6379/0"

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_mini_app_url: str = ""
    owner_chat_id: int = 0  # chat_id владельца для Wizard of Oz уведомлений

    # Marketplaces
    ozon_client_id: str = ""
    ozon_api_key: str = ""
    wb_cpa_subid: str = ""
    admitad_api_key: str = ""
    yandex_market_oauth: str = ""

    # ЮKassa
    yukassa_shop_id: str = ""
    yukassa_secret_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    # Misc
    env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"


settings = Settings()
