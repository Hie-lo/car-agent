from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import statistics


@dataclass
class PriceObservation:
    price_toman: int
    observed_at: datetime
    source_id: str
    listing_id: str


@dataclass
class BenchmarkResult:
    is_valid: bool
    median_price_toman: int | None = None
    sample_count: int = 0
    status_reason: str = ""


def calculate_price_benchmark(
    observations: list[PriceObservation],
    min_sample_count: int = 5,
    max_age_days: int = 30,
    reference_time: datetime | None = None,
) -> BenchmarkResult:
    """
    Computes market price benchmark from observations:
    - Deduplicates reposts of the same listing/vehicle
    - Filters out observations older than max_age_days
    - Requires at least min_sample_count unique valid observations
    - Uses median for robust benchmark
    """
    ref_time = reference_time or datetime.now(timezone.utc)

    # 1. Deduplicate reposts by (source_id, listing_id), keeping the latest observation
    unique_by_listing: dict[tuple[str, str], PriceObservation] = {}
    for obs in observations:
        key = (obs.source_id, obs.listing_id)
        if key not in unique_by_listing or obs.observed_at > unique_by_listing[key].observed_at:
            unique_by_listing[key] = obs

    deduped_samples = list(unique_by_listing.values())

    # 2. Filter out stale observations
    cutoff_date = ref_time - timedelta(days=max_age_days)
    fresh_samples = [obs for obs in deduped_samples if obs.observed_at >= cutoff_date]

    if len(fresh_samples) < min_sample_count:
        return BenchmarkResult(
            is_valid=False,
            sample_count=len(fresh_samples),
            status_reason="insufficient comparable data",
        )

    prices = [obs.price_toman for obs in fresh_samples]
    med = int(statistics.median(prices))

    return BenchmarkResult(
        is_valid=True,
        median_price_toman=med,
        sample_count=len(fresh_samples),
        status_reason="valid",
    )
