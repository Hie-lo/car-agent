from dataclasses import dataclass
from datetime import datetime


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
    - Requires at least min_sample_count unique valid observations, otherwise returns invalid with status 'insufficient comparable data'
    - Uses median for robust benchmark
    """
    raise NotImplementedError
