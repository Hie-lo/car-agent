import pytest
from app.domain.enums import BudgetMode, PriceMode
from app.domain.listing import Listing
from app.domain.vehicle_query import WatchRequest
from app.services.matching import evaluate_match


@pytest.fixture
def base_watch():
    return WatchRequest(
        id="watch_1",
        user_id=1001,
        make="پژو",
        model="207",
        budget_min=1_500_000_000,
        budget_max=1_700_000_000,
        budget_mode=BudgetMode.STRICT,
        max_overage_pct=0.0,
        hard_constraints={"gearbox": "automatic"},
    )


class TestMatchingAndBudgetRules:
    def test_strict_budget_excludes_above_ceiling(self, base_watch):
        listing = Listing(
            source_id="divar",
            source_listing_id="post_1",
            title="پژو 207 اتوماتیک",
            url="https://divar.ir/v/1",
            make="پژو",
            model="207",
            price_toman=1_750_000_000,  # 50M above ceiling
            gearbox="automatic",
            is_active=True,
        )
        result = evaluate_match(base_watch, listing)
        assert result.is_eligible is False
        assert "BUDGET_EXCEEDED" in result.reason_codes

    def test_flexible_budget_allows_near_budget_candidate(self, base_watch):
        base_watch.budget_mode = BudgetMode.FLEXIBLE
        base_watch.max_overage_pct = 3.5  # 1.75B is ~2.94% above 1.7B ceiling

        listing = Listing(
            source_id="divar",
            source_listing_id="post_1",
            title="پژو 207 اتوماتیک",
            url="https://divar.ir/v/1",
            make="پژو",
            model="207",
            price_toman=1_750_000_000,
            gearbox="automatic",
            is_active=True,
        )
        result = evaluate_match(base_watch, listing)
        assert result.is_eligible is True
        assert "PRICE_NEAR_BUDGET_FLEXIBLE" in result.reason_codes
        assert any("above" in r or "سقف" in r for r in result.reasons)

    def test_hard_constraint_never_bypassed_even_in_fallback(self, base_watch):
        # Watch requires automatic gearbox; listing is manual
        listing = Listing(
            source_id="divar",
            source_listing_id="post_2",
            title="پژو 207 دنده‌ای تمیز",
            url="https://divar.ir/v/2",
            make="پژو",
            model="207",
            price_toman=1_600_000_000,  # perfectly in budget
            gearbox="manual",           # violates hard constraint
            is_active=True,
        )
        # Even with allow_fallback=True, hard constraint violation must fail
        result = evaluate_match(base_watch, listing, allow_fallback=True)
        assert result.is_eligible is False
        assert "HARD_CONSTRAINT_VIOLATION" in result.reason_codes

    def test_missing_body_and_engine_condition_remains_unknown(self, base_watch):
        listing = Listing(
            source_id="divar",
            source_listing_id="post_3",
            title="پژو 207 اتومات",
            url="https://divar.ir/v/3",
            make="پژو",
            model="207",
            price_toman=1_650_000_000,
            gearbox="automatic",
            body_condition=None,   # missing
            engine_condition=None, # missing
            is_active=True,
        )
        result = evaluate_match(base_watch, listing)
        assert result.is_eligible is True
        # Missing fields should not give false "healthy" confidence
        assert "UNKNOWN_BODY_CONDITION" in result.reason_codes
        assert result.data_confidence < 100.0

    def test_inactive_listing_is_excluded(self, base_watch):
        listing = Listing(
            source_id="divar",
            source_listing_id="post_4",
            title="پژو 207 اتومات",
            url="https://divar.ir/v/4",
            make="پژو",
            model="207",
            price_toman=1_600_000_000,
            gearbox="automatic",
            is_active=False,
        )
        result = evaluate_match(base_watch, listing)
        assert result.is_eligible is False
        assert "INACTIVE_LISTING" in result.reason_codes
