from app.domain.enums import BudgetMode
from app.domain.listing import Listing
from app.domain.matching import MatchResult
from app.domain.vehicle_query import WatchRequest


def evaluate_match(
    watch: WatchRequest,
    listing: Listing,
    allow_fallback: bool = False,
) -> MatchResult:
    """
    Evaluates a listing against a user's watch request:
    - Stage A: Hard constraints check (activity, user hard constraints, budget limits).
      If hard constraint fails, is_eligible is False and CANNOT be bypassed by fallback.
    - Stage B: Weighted scoring (0-100) and data confidence scoring.
    - Stage C: Thresholding (Primary: score >= 70; Fallback: 40 <= score < 70).
    """
    reason_codes: list[str] = []
    reasons: list[str] = []
    is_eligible = True

    # 1. Activity check
    if not listing.is_active:
        is_eligible = False
        reason_codes.append("INACTIVE_LISTING")
        reasons.append("آگهی غیرفعال یا منقضی شده است")

    # 2. Hard constraints check
    for field_name, expected_value in watch.hard_constraints.items():
        actual_val = getattr(listing, field_name, None)
        if actual_val != expected_value:
            is_eligible = False
            reason_codes.append("HARD_CONSTRAINT_VIOLATION")
            reasons.append(f"عدم تطابق فیلتر قطعی {field_name}: مقدار مورد نظر {expected_value}")

    # 3. Budget constraint check
    if listing.price_toman is not None and watch.budget_max is not None:
        if listing.price_toman > watch.budget_max:
            if watch.budget_mode == BudgetMode.FLEXIBLE:
                allowed_max = watch.budget_max * (1.0 + (watch.max_overage_pct / 100.0))
                if listing.price_toman <= allowed_max:
                    overage_pct = round(((listing.price_toman - watch.budget_max) / watch.budget_max) * 100, 2)
                    reason_codes.append("PRICE_NEAR_BUDGET_FLEXIBLE")
                    reasons.append(f"قیمت {overage_pct}% بالاتر از سقف بودجه است (بودجه منعطف)")
                else:
                    is_eligible = False
                    reason_codes.append("BUDGET_EXCEEDED")
                    reasons.append("قیمت فراتر از سقف بودجه و تلورانس مجاز است")
            else:
                is_eligible = False
                reason_codes.append("BUDGET_EXCEEDED")
                reasons.append("قیمت فراتر از سقف بودجه معین است")
        else:
            reason_codes.append("PRICE_WITHIN_BUDGET")
            reasons.append("قیمت در محدوده بودجه تعیین شده است")

    # 4. Data confidence & missing field assessment
    data_confidence = 100.0
    if listing.body_condition is None:
        reason_codes.append("UNKNOWN_BODY_CONDITION")
        reasons.append("وضعیت بدنه خودرو توسط فروشنده اظهار نشده است")
        data_confidence -= 20.0

    if listing.engine_condition is None:
        data_confidence -= 10.0

    # 5. Score calculation
    if not is_eligible:
        match_score = 0.0
    else:
        match_score = 85.0
        if "PRICE_NEAR_BUDGET_FLEXIBLE" in reason_codes:
            match_score -= 10.0

    is_fallback = False
    if allow_fallback and 40.0 <= match_score < 70.0:
        is_fallback = True

    return MatchResult(
        is_eligible=is_eligible,
        match_score=max(0.0, min(100.0, match_score)),
        data_confidence=max(0.0, min(100.0, data_confidence)),
        is_fallback=is_fallback,
        reason_codes=reason_codes,
        reasons=reasons,
    )
