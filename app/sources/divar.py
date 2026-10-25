from datetime import datetime, timezone
import logging
from typing import Any
from app.config import settings
from app.domain.enums import PriceMode
from app.domain.listing import Listing
from app.sources.base import BaseListingSource

logger = logging.getLogger(__name__)

try:
    from kenar import Client, ClientConfig, GetPostRequest, SearchPostRequest
    KENAR_SDK_AVAILABLE = True
except ImportError:
    KENAR_SDK_AVAILABLE = False


class DivarKenarSource(BaseListingSource):
    BASE_WEB_URL = "https://divar.ir/v"

    def __init__(self, registry_entry, kenar_client: Any | None = None):
        super().__init__(registry_entry)
        self._kenar_client = kenar_client

    def get_client(self) -> Any:
        """Returns or initializes the official Kenar SDK Client."""
        if self._kenar_client is not None:
            return self._kenar_client

        if not KENAR_SDK_AVAILABLE:
            raise ImportError("The 'Kenar' SDK is not installed. Run: pip install Kenar")

        conf = ClientConfig(
            app_slug=settings.kenar_app_slug or "vehicle-radar",
            api_key=settings.kenar_api_key,
            oauth_secret=settings.kenar_oauth_secret or "dummy_secret",
            oauth_redirect_url=settings.kenar_oauth_redirect_url or "https://localhost/oauth",
        )
        self._kenar_client = Client(conf)
        return self._kenar_client

    def parse_post(self, raw_post: dict[str, Any]) -> Listing:
        """Parses a single post from Divar Kenar schema into canonical Listing."""
        token = raw_post.get("token", "")
        title = raw_post.get("title", "")
        url = f"{self.BASE_WEB_URL}/{token}" if token else ""

        # Price parsing
        price_info = raw_post.get("price") or {}
        price_val = price_info.get("value")
        price_type = price_info.get("type", "fixed")

        if price_type == "negotiable":
            price_mode = PriceMode.NEGOTIABLE
            price_toman = None
        elif price_val is not None:
            price_mode = PriceMode.FIXED
            price_toman = int(price_val)
        else:
            price_mode = PriceMode.UNKNOWN
            price_toman = None

        # Fields & vehicle specifications
        fields = raw_post.get("fields") or raw_post.get("data") or {}
        brand_model = fields.get("brand_model", "")
        if isinstance(brand_model, dict):
            brand_model = brand_model.get("value", "")

        parts = brand_model.split(" ", 1) if brand_model else ["", ""]
        make = parts[0] if parts else None
        model = parts[1] if len(parts) > 1 else None

        # Publication timestamp
        last_post_date = raw_post.get("last_post_date")
        if isinstance(last_post_date, (int, float)):
            observed_time = datetime.fromtimestamp(last_post_date, tz=timezone.utc)
        else:
            observed_time = datetime.now(timezone.utc)

        year_val = fields.get("year") if fields.get("year") is not None else fields.get("production-year")
        mileage_val = fields.get("mileage") if fields.get("mileage") is not None else fields.get("usage")
        body_val = fields.get("body_condition") if fields.get("body_condition") is not None else fields.get("body-status")

        return Listing(
            source_id="divar",
            source_listing_id=token,
            title=title,
            url=url,
            make=make or None,
            model=model or None,
            model_year=year_val,
            mileage=mileage_val,
            price_toman=price_toman,
            price_mode=price_mode,
            city=raw_post.get("city"),
            color=fields.get("color"),
            body_condition=body_val,
            gearbox=fields.get("gearbox"),
            is_active=True,
            first_observed=observed_time,
            last_observed=observed_time,
        )

    def parse_search_response(self, payload: dict[str, Any]) -> list[Listing]:
        """Parses full search response payload into a list of canonical Listings."""
        posts = payload.get("posts", [])
        return [self.parse_post(p) for p in posts]

    def search_live(
        self,
        city: str = "tehran",
        category: str = "light",
        query: dict[str, Any] | None = None,
        districts: list[str] | None = None,
    ) -> list[Listing]:
        """
        Executes search via the official Kenar SDK FinderService.
        Requires approved status.
        """
        self.check_runnable()
        client = self.get_client()

        req = SearchPostRequest(
            city=city,
            category=category,
            districts=districts or [],
            query=query or {},
        )
        response = client.finder.search_post(req)
        posts_data = response.posts if hasattr(response, "posts") and response.posts else []
        return [self.parse_post(p) for p in posts_data]

    def get_post_live(self, token: str) -> Listing:
        """Retrieves individual post detail via official Kenar SDK."""
        self.check_runnable()
        client = self.get_client()

        req = GetPostRequest(token=token)
        response = client.finder.get_post(req)
        raw_dict = response.dict() if hasattr(response, "dict") else dict(response)
        return self.parse_post(raw_dict)
