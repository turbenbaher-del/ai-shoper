from pydantic import BaseModel, Field


class ParsedRequest(BaseModel):
    category: str
    budget_max: int | None = None
    budget_min: int | None = None
    requirements: list[str] = Field(default_factory=list)
    use_case: str | None = None
    who_for: str | None = None
    keywords: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


class MarketplaceProduct(BaseModel):
    sku: str
    name: str
    marketplace: str
    price: int
    rating: float | None = None
    reviews_count: int | None = None
    image_url: str | None = None
    url: str
    specs: dict = Field(default_factory=dict)


class ReviewAnalysis(BaseModel):
    sku: str
    marketplace: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    fake_score: float = 0.0  # 0..1, чем выше тем подозрительнее
    reviews_analyzed: int = 0


class RankedProduct(BaseModel):
    rank: int
    sku: str
    marketplace: str
    name: str
    image_url: str | None = None
    reason: str
    score: float
    prices: list[dict]
    reviews_analyzed: int = 0
    fake_reviews_removed: int = 0


class PipelineResult(BaseModel):
    parsed_request: ParsedRequest
    products: list[RankedProduct]
    share_text: str
    needs_clarification: bool = False
    clarification_question: str | None = None
