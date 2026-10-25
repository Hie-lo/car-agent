import json
from pathlib import Path
import pytest
from app.domain.enums import PriceMode, SourceStatus
from app.sources.divar import DivarKenarSource
from app.sources.registry import SourceRegistryEntry


@pytest.fixture
def divar_fixture_payload():
    fixture_path = Path(__file__).parent.parent / "fixtures" / "divar_search_v2_sample.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def approved_divar_source():
    entry = SourceRegistryEntry(
        source_key="divar",
        display_name="Divar Kenar API",
        status=SourceStatus.APPROVED,
    )
    return DivarKenarSource(entry)


class TestDivarContract:
    def test_divar_parses_sample_fixture_correctly(self, approved_divar_source, divar_fixture_payload):
        listings = approved_divar_source.parse_search_response(divar_fixture_payload)
        assert len(listings) == 2

        # Post 1: Fixed price, complete vehicle fields
        l1 = listings[0]
        assert l1.source_id == "divar"
        assert l1.source_listing_id == "gZ123456"
        assert l1.url == "https://divar.ir/v/gZ123456"
        assert l1.price_toman == 680_000_000
        assert l1.price_mode == PriceMode.FIXED
        assert l1.model_year == 1401
        assert l1.mileage == 35_000
        assert l1.gearbox == "manual"
        assert l1.color == "سفید"
        assert l1.body_condition == "بدون رنگ"
        assert l1.city == "tehran"

        # Post 2: Negotiable price, omitted body condition
        l2 = listings[1]
        assert l2.source_listing_id == "gZ789012"
        assert l2.price_toman is None
        assert l2.price_mode == PriceMode.NEGOTIABLE
        assert l2.body_condition is None  # missing is None, never zero or healthy
        assert l2.mileage == 0

    def test_divar_fails_closed_when_not_approved(self):
        candidate_entry = SourceRegistryEntry(
            source_key="divar",
            display_name="Divar Kenar API",
            status=SourceStatus.CANDIDATE,  # not approved
        )
        source = DivarKenarSource(candidate_entry)
        with pytest.raises(PermissionError) as exc_info:
            source.check_runnable()
        assert "cannot run" in str(exc_info.value)
