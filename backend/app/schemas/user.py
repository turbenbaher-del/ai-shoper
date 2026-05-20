from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    tg_user_id: int
    tg_username: str | None
    tg_first_name: str | None
    quiz_completed: bool
    is_premium: bool
    premium_until: datetime | None
    free_searches_used: int
    push_consent: bool
    city: str | None = None

    model_config = {"from_attributes": True}


class AuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    user: UserOut
    token: str
    is_new: bool


class QuizData(BaseModel):
    who: str
    marketplaces: list[str]
    priority: str
    categories: list[str]
    city: str = ""


class PdnConsentRequest(BaseModel):
    consent: bool
