"""
Opt-in manual script to verify real Divar Kenar v2 API access and schema.
Usage:
    $env:DIVAR_API_KEY="your_real_key"
    python scripts/test_divar_api.py
"""
import json
import os
import sys
import urllib.error
import urllib.request


def test_divar_live_access():
    api_key = os.getenv("DIVAR_API_KEY")
    if not api_key:
        print("[INFO] DIVAR_API_KEY environment variable is not set.")
        print("To run live contract tests, set DIVAR_API_KEY and run again.")
        return 0

    base_url = os.getenv("DIVAR_BASE_URL", "https://api.divar.ir")
    endpoint = f"{base_url}/open-platform/v2/posts/search"
    
    headers = {
        "x-api-key": api_key,
        "User-Agent": "VehicleRadarAgent/0.1 (Milestone 0 contract test)",
        "Content-Type": "application/json",
    }
    
    # Bounded query (limit 2 results, car category)
    payload = {
        "query": "207",
        "category_slug": "light-cars",
        "limit": 2,
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    print(f"[TEST] Sending bounded request to {endpoint}...")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            rate_limit_remaining = resp.headers.get("x-ratelimit-remaining", "unknown")
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            print(f"[SUCCESS] Status: {status}, Rate-Limit-Remaining: {rate_limit_remaining}")
            print(f"[RESULT] Received {len(data.get('posts', []))} posts.")
            return 0
    except urllib.error.HTTPError as e:
        print(f"[HTTP ERROR] Code: {e.code}, Reason: {e.reason}")
        if e.code == 403:
            print("[NOTE] 403 Forbidden: Check API key or required SEARCH_POST scope.")
        elif e.code == 429:
            print("[NOTE] 429 Rate Limited: Honor Retry-After and throttle collector.")
        return 1
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_divar_live_access())
