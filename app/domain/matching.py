from dataclasses import dataclass, field


@dataclass
class MatchResult:
    is_eligible: bool
    match_score: float  # 0 to 100
    data_confidence: float  # 0 to 100
    is_fallback: bool = False
    reason_codes: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
