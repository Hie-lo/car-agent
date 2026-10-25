from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from app.domain.enums import BudgetMode, WatchStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WatchRequest:
    id: str
    user_id: int
    make: str
    model: str
    trim: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    budget_mode: BudgetMode = BudgetMode.STRICT
    max_overage_pct: float = 0.0  # e.g., 3.0 for 3%
    mileage_max: int | None = None
    city: str | None = None
    hard_constraints: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)
    expires_at: datetime | None = None
    status: WatchStatus = WatchStatus.ACTIVE
