from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserPlan:
    daily_request_credits: int = 5
    max_active_watches: int = 3
    watch_duration_days: int = 7


@dataclass
class UserCreditState:
    user_id: int
    daily_credits_remaining: int
    active_watches_count: int
    last_credit_reset: datetime


def can_create_watch(state: UserCreditState, plan: UserPlan) -> tuple[bool, str | None]:
    """
    Checks if a user can create a new watch request:
    - Must have remaining daily credits (> 0)
    - Must not exceed active_watches_count < plan.max_active_watches
    """
    raise NotImplementedError


def record_ledger_transaction(
    user_id: int,
    amount: int,
    transaction_type: str,
    idempotency_key: str,
) -> bool:
    """
    Appends an immutable credit transaction.
    Returns False if idempotency_key was already processed (idempotent).
    """
    raise NotImplementedError
