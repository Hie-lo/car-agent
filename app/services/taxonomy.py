from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Literal
from app.services.normalization import normalize_persian_text


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


def _calculate_similarity(s1: str, s2: str) -> float:
    # Token containment gives higher score for partial prefixes/extra words
    tokens1 = set(s1.split())
    tokens2 = set(s2.split())
    if tokens1 and tokens2:
        overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
    else:
        overlap = 0.0
    seq_ratio = SequenceMatcher(None, s1, s2).ratio()
    return max(overlap, seq_ratio)


def resolve_taxonomy(
    raw_text: str,
    entries: list[TaxonomyEntry],
    suggestion_threshold: float = 0.75,
) -> TaxonomyResolution:
    """
    Resolves user text against taxonomy entries:
    - exact match: normalized text matches canonical_name or an alias
    - suggestion: similarity >= suggestion_threshold
    - unknown: no entry meets the threshold
    Preserves original raw_text.
    """
    norm_input = normalize_persian_text(raw_text)
    if not norm_input:
        return TaxonomyResolution(raw_text=raw_text, match_type="unknown")

    best_entry: TaxonomyEntry | None = None
    best_score = 0.0
    is_exact = False

    for entry in entries:
        candidates = [entry.canonical_name] + list(entry.aliases)
        for cand in candidates:
            norm_cand = normalize_persian_text(cand)
            if norm_input == norm_cand:
                return TaxonomyResolution(
                    raw_text=raw_text,
                    match_type="exact",
                    entry=entry,
                    confidence=1.0,
                )
            score = _calculate_similarity(norm_input, norm_cand)
            if score > best_score:
                best_score = score
                best_entry = entry

    if best_entry and best_score >= suggestion_threshold:
        return TaxonomyResolution(
            raw_text=raw_text,
            match_type="suggestion",
            entry=best_entry,
            confidence=round(best_score, 2),
        )

    return TaxonomyResolution(
        raw_text=raw_text,
        match_type="unknown",
        entry=None,
        confidence=round(best_score, 2),
    )
