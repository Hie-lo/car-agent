"""
Script to test real Divar Kenar API access and schema using the official SDK.
Usage:
    $env:KENAR_API_KEY="your_api_key"
    $env:KENAR_APP_SLUG="your_app_slug"
    python scripts/test_divar_api.py
"""
import os
from pathlib import Path
import sys

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
        print("[INFO] KENAR_API_KEY is not set.")
        print("To test real live API access, configure in .env or set in terminal:")
        print("    $env:KENAR_API_KEY = \"your_real_key\"")
        print("    $env:KENAR_APP_SLUG = \"your_app_slug\"")
        return 0

    if not KENAR_AVAILABLE:
        print("[ERROR] The official 'Kenar' SDK is not installed.")
        print("Run: pip install Kenar")
        return 1

    print(f"[TEST] Initializing Kenar Client with App Slug: '{app_slug or 'vehicle-radar'}'...")
    conf = ClientConfig(
        app_slug=app_slug or "vehicle-radar",
        api_key=api_key,
        oauth_secret=os.getenv("KENAR_OAUTH_SECRET", "dummy_secret"),
        oauth_redirect_url=os.getenv("KENAR_OAUTH_REDIRECT_URL", "https://localhost/oauth"),
    )
    client = Client(conf)

    print("[TEST] Sending search request to Divar Finder service (category: 'light', city: 'tehran')...")
    try:
        # In Kenar SDK (Pydantic v2), all fields (city, category, districts, query) must be explicitly passed
        req = SearchPostRequest(
            city="tehran",
            category="light",
            districts=[],
            query={
                "brand_model": {"value": ["Pride 111 EX", "پژو 206"]},
            },
        )
        response = client.finder.search_post(req)
        posts = response.posts or []
        print(f"[SUCCESS] Search completed via Kenar SDK! Received {len(posts)} posts.")
        for i, post in enumerate(posts[:2], 1):
            print(f"  Post {i}: token={post.get('token')} title={post.get('title')}")
        return 0
    except Exception as e:
        err_msg = str(e)
        print(f"[HTTP/SDK ERROR] {err_msg}")
        if "403" in err_msg and "RBAC: access denied" in err_msg:
            print("\n" + "=" * 65)
            print("🔍 [DIAGNOSIS] علت ارور: دسترسی SEARCH_POST روی این کلید فعال نیست.")
            print("برای رفع این مشکل:")
            print("1. به پنل توسعه‌دهندگان کنار دیوار بروید: https://divar.ir/kenar")
            print(f"2. وارد تنظیمات برنامه '{app_slug}' شوید.")
            print("3. در بخش 'دسترسی‌ها / Scopes'، تیک دسترسی 'SEARCH_POST' و 'GET_POST' را فعال کنید.")
            print("4. در صورت نیاز به تایید پشتیبانی کنار برای جستجو، تیکت درخواست فعال‌سازی دسترسی سرچ ارسال کنید.")
            print("=" * 65 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(test_divar_sdk_access())
