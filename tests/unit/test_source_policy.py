import pytest
from app.domain.enums import SourceStatus
from app.sources.registry import (
    SourceRegistryEntry,
    can_run_source,
    handle_source_http_error,
)


class TestSourcePolicyAndSafety:
    def test_unapproved_sources_never_run(self):
        candidate = SourceRegistryEntry(source_key="divar", display_name="Divar", status=SourceStatus.CANDIDATE)
        paused = SourceRegistryEntry(source_key="bama", display_name="Bama", status=SourceStatus.PAUSED)
        blocked = SourceRegistryEntry(source_key="sheypoor", display_name="Sheypoor", status=SourceStatus.BLOCKED_BY_POLICY)
        disabled = SourceRegistryEntry(source_key="other", display_name="Other", status=SourceStatus.DISABLED)

        assert can_run_source(candidate) is False
        assert can_run_source(paused) is False
        assert can_run_source(blocked) is False
        assert can_run_source(disabled) is False

    def test_approved_source_can_run(self):
        approved = SourceRegistryEntry(source_key="divar", display_name="Divar", status=SourceStatus.APPROVED)
        assert can_run_source(approved) is True

    def test_source_403_or_401_triggers_pause_or_policy_block(self):
        entry = SourceRegistryEntry(source_key="divar", display_name="Divar", status=SourceStatus.APPROVED)
        handle_source_http_error(entry, status_code=403)
        assert entry.status in (SourceStatus.PAUSED, SourceStatus.BLOCKED_BY_POLICY)
        assert can_run_source(entry) is False

    def test_source_429_rate_limit_handling(self):
        entry = SourceRegistryEntry(source_key="divar", display_name="Divar", status=SourceStatus.APPROVED)
        handle_source_http_error(entry, status_code=429)
        # 429 should increment consecutive errors or pause
        assert entry.consecutive_errors > 0
