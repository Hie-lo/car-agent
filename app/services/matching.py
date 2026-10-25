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
    - Stage A: Hard constraints check (must be active, adhere to hard_constraints, budget check).
      If hard constraint fails, is_eligible is False and cannot be bypassed by fallback.
    - Stage B: Weighted scoring (0-100) and data confidence scoring.
    - Stage C: Thresholding (Primary: score >= 70; Fallback: 40 <= score < 70 only when allowed).
    """
    raise NotImplementedError
