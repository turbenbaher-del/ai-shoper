"""
Кросс-диалектные типы данных:
  - JsonB: JSONB на PostgreSQL, JSON на SQLite (для тестов)
  - TimestampTZ: TIMESTAMP WITH TIME ZONE на обоих
"""
from sqlalchemy import DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB


JsonB = JSON().with_variant(JSONB(), "postgresql")
TimestampTZ = DateTime(timezone=True)
