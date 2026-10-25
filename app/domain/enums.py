from enum import Enum


class Currency(str, Enum):
    TOMAN = "toman"
    RIAL = "rial"


class PriceMode(str, Enum):
    FIXED = "fixed"
    NEGOTIABLE = "negotiable"
    UNKNOWN = "unknown"


class ConstraintMode(str, Enum):
    HARD_CONSTRAINT = "hard_constraint"
    SOFT_PREFERENCE = "soft_preference"
    INFORMATIONAL = "informational"


class BudgetMode(str, Enum):
    STRICT = "strict"
    FLEXIBLE = "flexible"


class SourceStatus(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    PAUSED = "paused"
    DISABLED = "disabled"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class WatchStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
