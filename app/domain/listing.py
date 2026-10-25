from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.domain.enums import PriceMode


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Listing:
    source_id: str
    source_listing_id: str
    title: str
    url: str
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    model_year: int | None = None
    mileage: int | None = None
    price_toman: int | None = None
    price_mode: PriceMode = PriceMode.FIXED
    city: str | None = None
    color: str | None = None
    body_condition: str | None = None  # None means unknown, never inferred as healthy
    engine_condition: str | None = None  # None means unknown, never inferred as healthy
    gearbox: str | None = None
    fuel: str | None = None
    is_active: bool = True
    first_observed: datetime = field(default_factory=_utc_now)
    last_observed: datetime = field(default_factory=_utc_now)
