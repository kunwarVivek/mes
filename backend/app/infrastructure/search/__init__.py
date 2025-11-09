"""
Search infrastructure package.

Provides full-text search capabilities using ParadeDB pg_search (BM25).
"""
from app.infrastructure.search.pg_search_service import PgSearchService, SearchResult
from app.infrastructure.search.search_config import SearchConfig

__all__ = ["PgSearchService", "SearchResult", "SearchConfig"]
