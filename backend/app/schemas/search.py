from datetime import datetime

from pydantic import BaseModel


class ProductPrice(BaseModel):
    marketplace: str
    price: int
    url: str
    is_best: bool = False


class Product(BaseModel):
    rank: int
    name: str
    image_url: str | None
    reason: str
    prices: list[ProductPrice]
    sku: str
    marketplace: str


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    query_id: int
    query: str
    title: str
    subtitle: str
    products: list[Product]
    share_text: str
    processing_time_seconds: float
    needs_clarification: bool = False


class ClarificationResponse(BaseModel):
    needs_clarification: bool = True
    clarification: str


class QueryHistoryItem(BaseModel):
    id: int
    raw_text: str
    created_at: datetime
    products: list[Product]

    model_config = {"from_attributes": True}
