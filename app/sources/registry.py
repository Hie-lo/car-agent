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
    """Only APPROVED sources without an open circuit breaker are runnable."""
    if entry.is_circuit_open:
        return False
    return entry.status == SourceStatus.APPROVED


def handle_source_http_error(
    entry: SourceRegistryEntry,
    status_code: int,
) -> None:
    """
    Handles HTTP response errors:
    - 401/403: Marks source paused / blocked due to credential/permission failure
    - 429: Increments rate-limit backoff counter
    - 5xx: Tracks consecutive errors and opens circuit breaker if threshold reached
    """
    if status_code in (401, 403):
        entry.status = SourceStatus.PAUSED
        entry.consecutive_errors += 1
    elif status_code == 429:
        entry.consecutive_errors += 1
    elif status_code >= 500:
        entry.consecutive_errors += 1
        if entry.consecutive_errors >= 3:
            entry.is_circuit_open = True
