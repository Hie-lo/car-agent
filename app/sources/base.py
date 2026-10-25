from abc import ABC, abstractmethod
from typing import Any
from app.domain.listing import Listing
from app.sources.registry import SourceRegistryEntry, can_run_source


class BaseListingSource(ABC):
    def __init__(self, registry_entry: SourceRegistryEntry):
        self.registry_entry = registry_entry

    @abstractmethod
    def parse_post(self, raw_post: dict[str, Any]) -> Listing:
        """Normalizes raw source post payload into a canonical Listing object."""
        pass

    def check_runnable(self) -> None:
        """Fails closed if the source registry status is not approved."""
        if not can_run_source(self.registry_entry):
            raise PermissionError(
                f"Source '{self.registry_entry.source_key}' cannot run (status: {self.registry_entry.status.value})"
            )
