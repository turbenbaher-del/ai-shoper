from datetime import datetime

from pydantic import BaseModel


class TrackedItemCreate(BaseModel):
    marketplace: str
    sku: str
    name: str
    url: str
    image_url: str | None = None
    initial_price: int


class TrackedItemOut(BaseModel):
    id: int
    marketplace: str
    sku: str
    name: str
    url: str
    image_url: str | None
    initial_price: int
    current_price: int
    last_checked_at: datetime
    alert_threshold_pct: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryPoint(BaseModel):
    price: int
    captured_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionStatus(BaseModel):
    is_premium: bool
    plan: str | None
    expires_at: datetime | None
    status: str | None


class SubscriptionStartRequest(BaseModel):
    plan: str  # 'month', 'year', 'trial'
