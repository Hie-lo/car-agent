from app.domain.listing import Listing


def is_exact_duplicate(l1: Listing, l2: Listing) -> bool:
    """Returns True if both listings share the same source_id and source_listing_id."""
    raise NotImplementedError


def is_cross_source_duplicate(l1: Listing, l2: Listing, threshold: float = 0.85) -> bool:
    """
    Conservative cross-source duplicate detection based on attributes, location, price, mileage.
    Must not merge records solely because make/model/year/price are identical.
    """
    raise NotImplementedError


def should_renotify(
    previous: Listing,
    current: Listing,
    min_price_drop_pct: float = 3.0,
) -> bool:
    """
    Determines if a previously notified listing has undergone a material change warranting re-notification:
    - Significant price drop (>= min_price_drop_pct)
    - Reactivation from inactive state
    Insignificant changes (< min_price_drop_pct) do not trigger an alert.
    """
    raise NotImplementedError
