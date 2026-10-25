import pytest
from app.services.taxonomy import TaxonomyEntry, resolve_taxonomy


@pytest.fixture
def sample_taxonomy():
    return [
        TaxonomyEntry(
            id="peugeot_206_tip2",
            canonical_name="پژو ۲۰۶ تیپ ۲",
            aliases=["206 تیپ 2", "پژو 206 تیپ دو", "206 تیپ دو"],
        ),
        TaxonomyEntry(
            id="pride_131",
            canonical_name="پراید ۱۳۱",
            aliases=["پراید 131", "131"],
        ),
    ]


class TestTaxonomyResolution:
    def test_exact_taxonomy_hit(self, sample_taxonomy):
        res = resolve_taxonomy("پژو ۲۰۶ تیپ ۲", sample_taxonomy)
        assert res.match_type == "exact"
        assert res.entry is not None
        assert res.entry.id == "peugeot_206_tip2"
        assert res.confidence == 1.0

    def test_exact_alias_hit(self, sample_taxonomy):
        res = resolve_taxonomy("206 تیپ دو", sample_taxonomy)
        assert res.match_type == "exact"
        assert res.entry is not None
        assert res.entry.id == "peugeot_206_tip2"

    def test_close_taxonomy_suggestion(self, sample_taxonomy):
        # Slightly misspelled or partial input
        res = resolve_taxonomy("پژو 206 تیپ 2 فرانسوی", sample_taxonomy, suggestion_threshold=0.6)
        assert res.match_type in ("suggestion", "exact")
        assert res.entry is not None
        assert res.entry.id == "peugeot_206_tip2"

    def test_rejected_suggestion_preserves_raw_text(self, sample_taxonomy):
        raw = "خودروی سفارشی خاص"
        res = resolve_taxonomy(raw, sample_taxonomy)
        # When confirmed_by_user is False (rejected)
        res.confirmed_by_user = False
        assert res.raw_text == raw

    def test_unknown_taxonomy_entry(self, sample_taxonomy):
        res = resolve_taxonomy("سفینه فضایی مدل ۱۴۰۵", sample_taxonomy)
        assert res.match_type == "unknown"
        assert res.entry is None
        assert res.raw_text == "سفینه فضایی مدل ۱۴۰۵"
