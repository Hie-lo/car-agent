from dataclasses import dataclass
from app.domain.enums import SourceStatus


@dataclass
class SourceRegistryEntry:
    source_key: str
    display_name: str
    status: SourceStatus
    consecutive_errors: int = 0
    is_circuit_open: bool = False


def can_run_source(entry: SourceRegistryEntry) -> bool:
    """Only APPROVED sources are runnable. Any other status must fail closed."""
    raise NotImplementedError


def handle_source_http_error(
    entry: SourceRegistryEntry,
    status_code: int,
) -> None:
    """
    Handles HTTP response errors:
    - 401/403: Marks source paused / blocked due to credential/permission failure
    - 429: Increments rate-limit backoff or temporarily pauses
    - 5xx: Tracks consecutive errors and opens circuit breaker if threshold reached
    """
    raise NotImplementedError
