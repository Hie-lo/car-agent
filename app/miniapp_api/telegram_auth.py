import hashlib
import hmac
import time
import urllib.parse
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
    if not init_data_raw:
        return None

    try:
        parsed_items = urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True)
        data_dict = dict(parsed_items)
    except Exception:
        return None

    received_hash = data_dict.pop("hash", None)
    if not received_hash:
        return None

    # Construct data_check_string
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))

    # Compute secret key and hash
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    # Validate auth_date freshness
    auth_date_raw = data_dict.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        return None

    auth_date = int(auth_date_raw)
    now = current_timestamp if current_timestamp is not None else int(time.time())
    if now - auth_date > max_age_seconds:
        return None

    return data_dict
