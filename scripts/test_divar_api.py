"""
Script to test real Divar Kenar API access and schema using the official SDK.
Usage:
    $env:KENAR_API_KEY="your_api_key"
    $env:KENAR_APP_SLUG="your_app_slug"
    python scripts/test_divar_api.py
"""
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_dotenv

# Automatically load .env from root or current working directory
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(".env")

try:
    from kenar import Client, ClientConfig, SearchPostRequest
    KENAR_AVAILABLE = True
except ImportError:
    KENAR_AVAILABLE = False


def test_divar_sdk_access():
    api_key = os.getenv("KENAR_API_KEY") or os.getenv("DIVAR_API_KEY")
    app_slug = os.getenv("KENAR_APP_SLUG") or os.getenv("DIVAR_APP_SLUG")

    if not api_key:
        print("[INFO] KENAR_API_KEY is not set in .env.")
        return 0

    print("=" * 65)
    print(f"📡 [DIAGNOSTIC] App Slug: '{app_slug}' | Key prefix: '{api_key[:6]}...'")
    print("=" * 65)

    headers = {
        "x-api-key": api_key,
        "User-Agent": "VehicleRadarAgent/0.1",
        "Content-Type": "application/json",
    }

    # Test 1: Check Asset Endpoint (Does the API key work at all?)
    print("\n[TEST 1] Testing Asset Service (GET /v1/open-platform/assets/city)...")
    try:
        import urllib.request
        req = urllib.request.Request("https://api.divar.ir/v1/open-platform/assets/city", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"  --> Status: {resp.status} (Asset API key is VALID and recognized!)")
    except urllib.error.HTTPError as e:
        print(f"  --> Status: {e.code} ({e.reason}) - Detail: {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"  --> Failed: {e}")

    # Test 2: Kenar SDK Finder v1 (POST /v1/open-platform/finder/post)
    print("\n[TEST 2] Testing Finder v1 (POST /v1/open-platform/finder/post)...")
    try:
        payload = json.dumps({
            "city": "tehran",
            "category": "light",
            "districts": [],
            "query": {"brand_model": {"value": ["Pride 111 EX", "پژو 206"]}},
        }).encode("utf-8")
        req = urllib.request.Request("https://api.divar.ir/v1/open-platform/finder/post", data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  --> Status: {resp.status} (SUCCESS! Returned {len(data.get('posts', []))} posts)")
    except urllib.error.HTTPError as e:
        print(f"  --> Status: {e.code} ({e.reason}) - Detail: {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"  --> Failed: {e}")

    # Test 3: Kenar Finder v2 (POST /open-platform/v2/posts/search)
    print("\n[TEST 3] Testing Finder v2 (POST /open-platform/v2/posts/search)...")
    try:
        payload_v2 = json.dumps({
            "query": "206",
            "category_slug": "light-cars",
            "limit": 2,
        }).encode("utf-8")
        req = urllib.request.Request("https://api.divar.ir/open-platform/v2/posts/search", data=payload_v2, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  --> Status: {resp.status} (SUCCESS! Returned {len(data.get('posts', []))} posts)")
    except urllib.error.HTTPError as e:
        print(f"  --> Status: {e.code} ({e.reason}) - Detail: {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"  --> Failed: {e}")

    print("\n" + "=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(test_divar_sdk_access())
