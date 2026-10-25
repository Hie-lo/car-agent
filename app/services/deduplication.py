from app.domain.listing import Listing
from app.services.normalization import normalize_persian_text


def is_exact_duplicate(l1: Listing, l2: Listing) -> bool:
    """Returns True if both listings share the same source_id and source_listing_id."""
    return bool(l1.source_id and l2.source_id and
                l1.source_listing_id and l2.source_listing_id and
                l1.source_id == l2.source_id and
                l1.source_listing_id == l2.source_listing_id)


def is_cross_source_duplicate(l1: Listing, l2: Listing, threshold: float = 0.85) -> bool:
    """
    Conservative cross-source duplicate detection.
    Must NOT merge records solely on make/model/year/price if city, mileage, or color differ.
    """
    # 1. Negative checks: if year, city, or mileage diverge significantly, they are distinct cars
    if l1.model_year is not None and l2.model_year is not None:
        if l1.model_year != l2.model_year:
            return False

    if l1.city and l2.city:
        if normalize_persian_text(l1.city) != normalize_persian_text(l2.city):
            return False

    if l1.mileage is not None and l2.mileage is not None:
        mileage_diff = abs(l1.mileage - l2.mileage)
        if mileage_diff > 1000:
            return False

    # 2. Positive checks: must have same make/model and close price
    if l1.make and l2.make:
        if normalize_persian_text(l1.make) != normalize_persian_text(l2.make):
            return False

    if l1.model and l2.model:
        if normalize_persian_text(l1.model) != normalize_persian_text(l2.model):
            return False

    if l1.price_toman is not None and l2.price_toman is not None:
        price_diff_pct = abs(l1.price_toman - l2.price_toman) / max(l1.price_toman, 1)
        if price_diff_pct > 0.05:  # more than 5% difference
            return False

    return True


def should_renotify(
    previous: Listing,
    current: Listing,
    min_price_drop_pct: float = 3.0,
) -> bool:
    """
    Determines if a previously notified listing has undergone a material change:
    - Significant price drop (>= min_price_drop_pct)
    - Reactivation from inactive state
    Minor fluctuations (< min_price_drop_pct) do not trigger an alert.
    """
    # Check reactivation
    if not previous.is_active and current.is_active:
        return True

    # Check meaningful price reduction
    if previous.price_toman is not None and current.price_toman is not None:
        if previous.price_toman > 0:
            price_drop = previous.price_toman - current.price_toman
            drop_percentage = (price_drop / previous.price_toman) * 100.0
            if drop_percentage >= min_price_drop_pct:
                return True

    return False
