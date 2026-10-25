from datetime import datetime, timezone
from typing import Any
from app.domain.enums import PriceMode
from app.domain.listing import Listing
from app.sources.base import BaseListingSource


class DivarKenarSource(BaseListingSource):
    BASE_WEB_URL = "https://divar.ir/v"

    def parse_post(self, raw_post: dict[str, Any]) -> Listing:
        """Parses a single post from Divar Kenar v2 schema into canonical Listing."""
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
        fields = raw_post.get("fields") or {}
        brand_model = fields.get("brand_model", "")
        parts = brand_model.split(" ", 1) if brand_model else ["", ""]
        make = parts[0] if parts else None
        model = parts[1] if len(parts) > 1 else None

        # Publication timestamp
        last_post_date = raw_post.get("last_post_date")
        observed_time = (
            datetime.fromtimestamp(last_post_date, tz=timezone.utc)
            if last_post_date
            else datetime.now(timezone.utc)
        )

        return Listing(
            source_id="divar",
            source_listing_id=token,
            title=title,
            url=url,
            make=make or None,
            model=model or None,
            model_year=fields.get("year"),
            mileage=fields.get("mileage"),
            price_toman=price_toman,
            price_mode=price_mode,
            city=raw_post.get("city"),
            color=fields.get("color"),
            body_condition=fields.get("body_condition"),  # None if omitted
            gearbox=fields.get("gearbox"),
            is_active=True,
            first_observed=observed_time,
            last_observed=observed_time,
        )

    def parse_search_response(self, payload: dict[str, Any]) -> list[Listing]:
        """Parses full search response payload into a list of canonical Listings."""
        posts = payload.get("posts", [])
        return [self.parse_post(p) for p in posts]
