import pytest
from app.domain.listing import Listing
from app.services.deduplication import (
    is_cross_source_duplicate,
    is_exact_duplicate,
    should_renotify,
)


class TestDeduplication:
    def test_same_source_listing_exact_duplicate(self):
        l1 = Listing(
            source_id="divar",
            source_listing_id="token_123",
            title="تارا اتوماتیک V4",
            url="https://divar.ir/v/123",
            price_toman=950_000_000,
        )
        l2 = Listing(
            source_id="divar",
            source_listing_id="token_123",
            title="تارا اتوماتیک V4 صفر",
            url="https://divar.ir/v/123",
            price_toman=950_000_000,
        )
        assert is_exact_duplicate(l1, l2) is True

    def test_different_source_listing_id_not_exact_duplicate(self):
        l1 = Listing(
            source_id="divar",
            source_listing_id="token_123",
            title="تارا",
            url="https://divar.ir/v/123",
        )
        l2 = Listing(
            source_id="divar",
            source_listing_id="token_456",
            title="تارا",
            url="https://divar.ir/v/456",
        )
        assert is_exact_duplicate(l1, l2) is False

    def test_cross_source_probable_duplicate(self):
        l1 = Listing(
            source_id="divar",
            source_listing_id="divar_1",
            title="دنا پلاس توربو اتوماتیک ۱۴۰۲ سفید",
            url="https://divar.ir/v/d1",
            make="ایران خودرو",
            model="دنا پلاس",
            model_year=1402,
            mileage=15_000,
            price_toman=1_050_000_000,
            city="تهران",
            color="سفید",
        )
        l2 = Listing(
            source_id="bama",
            source_listing_id="bama_1",
            title="دنا پلاس توربو اتومات 1402 سفید",
            url="https://bama.ir/car/b1",
            make="ایران خودرو",
            model="دنا پلاس",
            model_year=1402,
            mileage=15_000,
            price_toman=1_050_000_000,
            city="تهران",
            color="سفید",
        )
        assert is_cross_source_duplicate(l1, l2) is True

    def test_similar_but_different_vehicles_not_merged(self):
        # Same make/model/year/price but completely different mileage and city
        l1 = Listing(
            source_id="divar",
            source_listing_id="divar_2",
            title="۲۰۶ سفید",
            url="https://divar.ir/v/d2",
            make="پژو",
            model="206",
            model_year=1399,
            mileage=20_000,
            price_toman=450_000_000,
            city="تهران",
        )
        l2 = Listing(
            source_id="bama",
            source_listing_id="bama_2",
            title="۲۰۶ مشکی",
            url="https://bama.ir/car/b2",
            make="پژو",
            model="206",
            model_year=1399,
            mileage=180_000,  # huge mileage difference
            price_toman=450_000_000,
            city="مشهد",       # different city
        )
        assert is_cross_source_duplicate(l1, l2) is False

    def test_material_price_drop_triggers_renotification(self):
        prev = Listing(
            source_id="divar",
            source_listing_id="post_99",
            title="هایما S7",
            url="https://divar.ir/v/99",
            price_toman=1_600_000_000,
        )
        # 5% price drop (1.6B -> 1.52B is -80M = -5%)
        curr = Listing(
            source_id="divar",
            source_listing_id="post_99",
            title="هایما S7",
            url="https://divar.ir/v/99",
            price_toman=1_520_000_000,
        )
        assert should_renotify(prev, curr, min_price_drop_pct=3.0) is True

    def test_insignificant_price_drop_does_not_trigger_renotification(self):
        prev = Listing(
            source_id="divar",
            source_listing_id="post_99",
            title="هایما S7",
            url="https://divar.ir/v/99",
            price_toman=1_600_000_000,
        )
        # Less than 1% change (1.6B -> 1.595B)
        curr = Listing(
            source_id="divar",
            source_listing_id="post_99",
            title="هایما S7",
            url="https://divar.ir/v/99",
            price_toman=1_595_000_000,
        )
        assert should_renotify(prev, curr, min_price_drop_pct=3.0) is False
