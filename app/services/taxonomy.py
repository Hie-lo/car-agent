from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class TaxonomyEntry:
    id: str
    canonical_name: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class TaxonomyResolution:
    raw_text: str
    match_type: Literal["exact", "suggestion", "unknown"]
    entry: TaxonomyEntry | None = None
    confidence: float = 0.0
    confirmed_by_user: bool | None = None


def resolve_taxonomy(
    raw_text: str,
    entries: list[TaxonomyEntry],
    suggestion_threshold: float = 0.75,
) -> TaxonomyResolution:
    """
    Resolves user text against taxonomy entries.
    Returns:
    - exact match if text or alias matches normalized entry
    - suggestion if text is close (above threshold)
    - unknown otherwise
    Never mutates original raw_text.
    """
    raise NotImplementedError
