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


# In-memory store for idempotency keys (in production backed by DB unique constraint)
_PROCESSED_IDEMPOTENCY_KEYS: set[str] = set()


def can_create_watch(state: UserCreditState, plan: UserPlan) -> tuple[bool, str | None]:
    """
    Checks if a user can create a new watch request:
    - Must have remaining daily credits (> 0)
    - Must not exceed active_watches_count < plan.max_active_watches
    """
    if state.daily_credits_remaining <= 0:
        return False, "INSUFFICIENT_DAILY_CREDITS"

    if state.active_watches_count >= plan.max_active_watches:
        return False, "ACTIVE_WATCHES_CAP_REACHED"

    return True, None


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
    if idempotency_key in _PROCESSED_IDEMPOTENCY_KEYS:
        return False

    _PROCESSED_IDEMPOTENCY_KEYS.add(idempotency_key)
    return True
