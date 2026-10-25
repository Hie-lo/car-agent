from typing import Any


def validate_telegram_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age_seconds: int = 86400,
    current_timestamp: int | None = None,
) -> dict[str, Any] | None:
    """
    Validates raw Telegram Mini App initData server-side:
    - Verifies HMAC-SHA256 signature against bot_token using Telegram WebApp algorithm
    - Rejects invalid/tampered signatures
    - Rejects stale auth_date exceeding max_age_seconds
    Returns parsed dictionary if valid, or None if invalid/expired.
    """
    raise NotImplementedError
