"""
PostgreSQL-native caching service using UNLOGGED table.

This service provides a Redis-like caching interface backed by PostgreSQL's
UNLOGGED table feature, which provides 2x faster writes and 1-2ms latency.

Benefits over Redis:
- No additional infrastructure (single PostgreSQL instance)
- Transactional consistency with application data
- Simpler backup/restore (single database backup)
- Lower operational complexity

Trade-offs:
- Slightly slower than Redis (<1ms vs 1-2ms)
- Data not replicated (UNLOGGED tables not in WAL)
- Cleared on database crash (acceptable for cache)
"""
import json
from datetime import datetime, timedelta
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


class CacheService:
    """
    PostgreSQL-native caching service using UNLOGGED table.

    Usage:
        cache = CacheService(db)
        cache.set("dashboard:oee:plant1", {"oee": 85.5}, ttl=900)  # 15 minutes
        value = cache.get("dashboard:oee:plant1")
        cache.delete("dashboard:oee:plant1")
        cache.clear_expired()
    """

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value (dict/list/str/int/float) or None if not found or expired
        """
        result = self.db.execute(
            text("""
                SELECT cache_value, expires_at
                FROM cache
                WHERE cache_key = :key
            """),
            {"key": key}
        ).fetchone()

        if not result:
            return None

        cache_value, expires_at = result

        # Check if expired
        if datetime.now() > expires_at:
            # Delete expired entry
            self.delete(key)
            return None

        # Return deserialized value
        return cache_value

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Store value in cache with expiration.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (default: 3600 = 1 hour)
        """
        expires_at = datetime.now() + timedelta(seconds=ttl)

        # Upsert (INSERT ... ON CONFLICT UPDATE)
        self.db.execute(
            text("""
                INSERT INTO cache (cache_key, cache_value, expires_at)
                VALUES (:key, :value::jsonb, :expires_at)
                ON CONFLICT (cache_key)
                DO UPDATE SET
                    cache_value = EXCLUDED.cache_value,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
            """),
            {
                "key": key,
                "value": json.dumps(value),
                "expires_at": expires_at
            }
        )
        self.db.commit()

    def delete(self, key: str) -> bool:
        """
        Delete cached value by key.

        Args:
            key: Cache key

        Returns:
            True if key existed, False otherwise
        """
        result = self.db.execute(
            text("""
                DELETE FROM cache
                WHERE cache_key = :key
                RETURNING cache_key
            """),
            {"key": key}
        )
        self.db.commit()
        return result.rowcount > 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and valid, False otherwise
        """
        return self.get(key) is not None

    def clear_expired(self) -> int:
        """
        Remove all expired cache entries.

        This should be called periodically (e.g., every 5 minutes via pg_cron)
        to prevent UNLOGGED table from growing indefinitely.

        Returns:
            Number of entries deleted
        """
        result = self.db.execute(
            text("SELECT cleanup_expired_cache()")
        )
        deleted_count = result.scalar()
        self.db.commit()
        return deleted_count

    def clear_all(self) -> None:
        """
        Clear all cache entries (use with caution).

        Useful for testing or manual cache invalidation.
        """
        self.db.execute(text("TRUNCATE cache"))
        self.db.commit()

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with total_entries, expired_entries, cache_size_mb
        """
        result = self.db.execute(
            text("""
                SELECT
                    COUNT(*) as total_entries,
                    COUNT(*) FILTER (WHERE expires_at < NOW()) as expired_entries,
                    pg_total_relation_size('cache') / 1024.0 / 1024.0 as cache_size_mb
                FROM cache
            """)
        ).fetchone()

        return {
            "total_entries": result[0],
            "expired_entries": result[1],
            "cache_size_mb": round(result[2], 2)
        }

    # Convenience methods for common cache patterns

    def cache_dashboard(self, dashboard_key: str, data: dict, ttl: int = 900) -> None:
        """
        Cache dashboard data with 15-minute default TTL.

        Args:
            dashboard_key: Dashboard identifier (e.g., "oee:plant1")
            data: Dashboard data
            ttl: Time to live in seconds (default: 900 = 15 minutes)
        """
        key = f"dashboard:{dashboard_key}"
        self.set(key, data, ttl)

    def get_dashboard(self, dashboard_key: str) -> Optional[dict]:
        """
        Retrieve cached dashboard data.

        Args:
            dashboard_key: Dashboard identifier

        Returns:
            Cached dashboard data or None
        """
        key = f"dashboard:{dashboard_key}"
        return self.get(key)

    def cache_metrics(self, metric_type: str, filters: dict, data: dict, ttl: int = 300) -> None:
        """
        Cache metrics calculation with 5-minute default TTL.

        Args:
            metric_type: Metric type (e.g., "oee", "fpy", "otd")
            filters: Query filters (plant_id, date_range, etc.)
            data: Metrics data
            ttl: Time to live in seconds (default: 300 = 5 minutes)
        """
        # Create cache key from filters
        filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()))
        key = f"metrics:{metric_type}:{filter_str}"
        self.set(key, data, ttl)

    def get_metrics(self, metric_type: str, filters: dict) -> Optional[dict]:
        """
        Retrieve cached metrics.

        Args:
            metric_type: Metric type
            filters: Query filters

        Returns:
            Cached metrics data or None
        """
        filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()))
        key = f"metrics:{metric_type}:{filter_str}"
        return self.get(key)


def get_cache_service(db: Session) -> CacheService:
    """
    Dependency injection factory for CacheService.

    Usage in FastAPI:
        @router.get("/dashboard")
        def get_dashboard(cache: CacheService = Depends(get_cache_service)):
            cached = cache.get_dashboard("oee:plant1")
            if cached:
                return cached
            # ... compute and cache
    """
    return CacheService(db)
