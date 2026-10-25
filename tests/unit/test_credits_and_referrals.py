from datetime import datetime, timezone
import pytest
from app.services.credits import (
    UserCreditState,
    UserPlan,
    can_create_watch,
    record_ledger_transaction,
)
from app.services.referrals import process_referral_reward


class TestCreditsAndPlans:
    def test_cannot_create_watch_when_daily_credits_zero(self):
        plan = UserPlan(daily_request_credits=5, max_active_watches=3)
        state = UserCreditState(
            user_id=1,
            daily_credits_remaining=0,  # exhausted
            active_watches_count=1,
            last_credit_reset=datetime.now(timezone.utc),
        )
        allowed, reason = can_create_watch(state, plan)
        assert allowed is False
        assert reason == "INSUFFICIENT_DAILY_CREDITS"

    def test_cannot_create_watch_when_active_cap_reached(self):
        plan = UserPlan(daily_request_credits=5, max_active_watches=3)
        state = UserCreditState(
            user_id=1,
            daily_credits_remaining=4,
            active_watches_count=3,  # reached cap
            last_credit_reset=datetime.now(timezone.utc),
        )
        allowed, reason = can_create_watch(state, plan)
        assert allowed is False
        assert reason == "ACTIVE_WATCHES_CAP_REACHED"

    def test_can_create_watch_within_limits(self):
        plan = UserPlan(daily_request_credits=5, max_active_watches=3)
        state = UserCreditState(
            user_id=1,
            daily_credits_remaining=2,
            active_watches_count=1,
            last_credit_reset=datetime.now(timezone.utc),
        )
        allowed, reason = can_create_watch(state, plan)
        assert allowed is True
        assert reason is None

    def test_ledger_transaction_idempotency(self):
        key = "spend_user_1_watch_999"
        # First transaction succeeds
        first = record_ledger_transaction(user_id=1, amount=-1, transaction_type="spend", idempotency_key=key)
        assert first is True

        # Second transaction with same key must be rejected (idempotent)
        second = record_ledger_transaction(user_id=1, amount=-1, transaction_type="spend", idempotency_key=key)
        assert second is False


class TestReferrals:
    def test_referral_grants_reward_only_once(self):
        referrer = 100
        referee = 200
        # First qualified referral gives reward
        rewarded_first = process_referral_reward(referrer, referee, reward_credits=2)
        assert rewarded_first is True

        # Repeated invite for same referee must not grant recurring reward
        rewarded_second = process_referral_reward(referrer, referee, reward_credits=2)
        assert rewarded_second is False
