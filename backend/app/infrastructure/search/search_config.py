"""
Search configuration for pg_search service.

Configures BM25 search parameters and fallback behavior.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchConfig:
    """
    Configuration for PgSearchService.

    Controls pg_search usage, BM25 parameters, and fallback behavior.
    """

    use_pg_search: bool = False
    """Whether to use pg_search extension (default: False for testing)."""

    default_limit: int = 20
    """Default maximum results to return."""

    max_limit: int = 100
    """Maximum allowed limit to prevent excessive results."""

    bm25_k1: float = 1.2
    """BM25 k1 parameter (term frequency saturation, default: 1.2)."""

    bm25_b: float = 0.75
    """BM25 b parameter (length normalization, default: 0.75)."""

    enable_fuzzy: bool = False
    """Enable fuzzy matching for typos (default: False)."""

    fuzzy_distance: int = 2
    """Maximum edit distance for fuzzy matching (default: 2)."""

    def validate_limit(self, limit: Optional[int]) -> int:
        """
        Validate and normalize limit parameter.

        Args:
            limit: Requested limit

        Returns:
            Validated limit within allowed range
        """
        if limit is None or limit <= 0:
            return self.default_limit

        return min(limit, self.max_limit)
