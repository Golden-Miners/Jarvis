from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from jarvis.schemas.models import Candle, Forecast, MarketStructure, NewsImpact


class StrategyContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1)
    candles: dict[str, list[Candle]]
    market_structure: MarketStructure
    news: NewsImpact | None = None
    forecast: Forecast | None = None
    now: datetime

    @field_validator("now")
    @classmethod
    def now_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("now must include a timezone")
        return value.astimezone(UTC)
