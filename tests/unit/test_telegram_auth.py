import hashlib
import hmac
import time
import urllib.parse
import pytest
from app.miniapp_api.telegram_auth import validate_telegram_init_data


def generate_valid_init_data(bot_token: str, auth_date: int, user_json: str = '{"id":123456,"first_name":"Ali"}') -> str:
    params = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": user_json,
    }
    # Secret key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    
    # Data check string: key=val sorted by key joined with \n
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    calc_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    
    params["hash"] = calc_hash
    return urllib.parse.urlencode(params)


class TestTelegramMiniAppAuth:
    bot_token = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"

    def test_valid_init_data_passes(self):
        now = int(time.time())
        valid_query = generate_valid_init_data(self.bot_token, auth_date=now)
        result = validate_telegram_init_data(
            valid_query,
            self.bot_token,
            max_age_seconds=86400,
            current_timestamp=now,
        )
        assert result is not None
        assert result.get("auth_date") == str(now)
        assert "user" in result

    def test_tampered_init_data_rejected(self):
        now = int(time.time())
        valid_query = generate_valid_init_data(self.bot_token, auth_date=now)
        # Tamper query parameters
        tampered_query = valid_query.replace("123456", "999999")
        result = validate_telegram_init_data(
            tampered_query,
            self.bot_token,
            max_age_seconds=86400,
            current_timestamp=now,
        )
        assert result is None

    def test_stale_auth_date_rejected(self):
        now = int(time.time())
        stale_time = now - 90000  # older than 86400 seconds (24h)
        stale_query = generate_valid_init_data(self.bot_token, auth_date=stale_time)
        result = validate_telegram_init_data(
            stale_query,
            self.bot_token,
            max_age_seconds=86400,
            current_timestamp=now,
        )
        assert result is None
