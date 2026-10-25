from datetime import datetime, timedelta
import pytest
from app.services.price_benchmark import (
    PriceObservation,
    calculate_price_benchmark,
)


class TestPriceBenchmark:
    now = datetime(2026, 10, 25, 12, 0, 0)

    def test_insufficient_samples_rejected(self):
        # Only 2 samples when minimum 5 required
        samples = [
            PriceObservation(price_toman=500_000_000, observed_at=self.now, source_id="divar", listing_id="p1"),
            PriceObservation(price_toman=520_000_000, observed_at=self.now, source_id="divar", listing_id="p2"),
        ]
        result = calculate_price_benchmark(samples, min_sample_count=5, reference_time=self.now)
        assert result.is_valid is False
        assert "insufficient comparable data" in result.status_reason.lower()

    def test_reposts_deduplicated_before_benchmarking(self):
        # 5 records, but 4 of them are repeated reposts of the same listing_id
        samples = [
            PriceObservation(price_toman=600_000_000, observed_at=self.now, source_id="divar", listing_id="repost_1"),
            PriceObservation(price_toman=600_000_000, observed_at=self.now, source_id="divar", listing_id="repost_1"),
            PriceObservation(price_toman=600_000_000, observed_at=self.now, source_id="divar", listing_id="repost_1"),
            PriceObservation(price_toman=600_000_000, observed_at=self.now, source_id="divar", listing_id="repost_1"),
            PriceObservation(price_toman=620_000_000, observed_at=self.now, source_id="divar", listing_id="distinct_2"),
        ]
        # Only 2 unique listings exist; with min_sample_count=5, this must fail
        result = calculate_price_benchmark(samples, min_sample_count=5, reference_time=self.now)
        assert result.is_valid is False
        assert result.sample_count == 2

    def test_stale_data_filtered_out(self):
        # 5 samples, but 2 are 45 days old (> max_age_days=30)
        samples = [
            PriceObservation(price_toman=700_000_000, observed_at=self.now, source_id="divar", listing_id="l1"),
            PriceObservation(price_toman=710_000_000, observed_at=self.now, source_id="divar", listing_id="l2"),
            PriceObservation(price_toman=720_000_000, observed_at=self.now, source_id="divar", listing_id="l3"),
            PriceObservation(price_toman=680_000_000, observed_at=self.now - timedelta(days=45), source_id="divar", listing_id="l4"),
            PriceObservation(price_toman=690_000_000, observed_at=self.now - timedelta(days=50), source_id="divar", listing_id="l5"),
        ]
        result = calculate_price_benchmark(samples, min_sample_count=5, max_age_days=30, reference_time=self.now)
        assert result.is_valid is False  # only 3 fresh samples remain

    def test_valid_benchmark_computes_median_robustly(self):
        # 5 distinct fresh samples with an extreme outlier (10B)
        samples = [
            PriceObservation(price_toman=800_000_000, observed_at=self.now, source_id="divar", listing_id="s1"),
            PriceObservation(price_toman=810_000_000, observed_at=self.now, source_id="divar", listing_id="s2"),
            PriceObservation(price_toman=820_000_000, observed_at=self.now, source_id="divar", listing_id="s3"),
            PriceObservation(price_toman=830_000_000, observed_at=self.now, source_id="divar", listing_id="s4"),
            PriceObservation(price_toman=10_000_000_000, observed_at=self.now, source_id="divar", listing_id="s5"),  # outlier
        ]
        result = calculate_price_benchmark(samples, min_sample_count=5, reference_time=self.now)
        assert result.is_valid is True
        # Median of [800M, 810M, 820M, 830M, 10000M] is 820M
        assert result.median_price_toman == 820_000_000
