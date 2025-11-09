"""
Integration tests for PostgreSQL extensions installation.

Tests verify that all required extensions are properly installed:
- pgmq: Message queue for async job processing
- pg_search: BM25 full-text search capabilities
- pg_duckdb: Analytics and OLAP query acceleration
- timescaledb: Time-series data compression and optimization
- pg_cron: Job scheduler for periodic tasks
"""
import pytest
from sqlalchemy import text
from app.core.database import engine
from app.core.extensions import (
    verify_extensions_installed,
    get_extension_versions,
    REQUIRED_EXTENSIONS
)


class TestPostgreSQLExtensions:
    """Test suite for PostgreSQL extensions installation and verification."""

    def test_all_extensions_installed(self):
        """
        Test that all required extensions are installed.

        This test will FAIL initially (RED phase) until migration is applied.
        """
        with engine.connect() as conn:
            result = verify_extensions_installed(conn)
            assert result is True, "Not all required extensions are installed"

    def test_extension_versions(self):
        """
        Test that extension versions can be retrieved.

        Verifies that extensions are not only installed but also queryable.
        """
        with engine.connect() as conn:
            versions = get_extension_versions(conn)

            # All required extensions should have version information
            for ext_name in REQUIRED_EXTENSIONS:
                assert ext_name in versions, f"Extension {ext_name} not found in versions"
                assert versions[ext_name] is not None, f"Extension {ext_name} has no version"
                assert len(versions[ext_name]) > 0, f"Extension {ext_name} version is empty"

    def test_pgmq_functionality(self):
        """
        Test that pgmq extension is functional.

        Verifies basic message queue operations work.
        """
        with engine.connect() as conn:
            # Check if pgmq functions are available
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'pgmq_create');"
            ))
            pgmq_available = result.scalar()
            assert pgmq_available is True, "pgmq_create function not available"

    def test_pg_search_functionality(self):
        """
        Test that pg_search extension is functional.

        Verifies BM25 search functions are available.
        """
        with engine.connect() as conn:
            # Check if pg_search schema exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'paradedb');"
            ))
            pg_search_available = result.scalar()
            assert pg_search_available is True, "paradedb schema not available for pg_search"

    def test_pg_duckdb_functionality(self):
        """
        Test that pg_duckdb extension is functional.

        Verifies DuckDB analytics functions are available.
        """
        with engine.connect() as conn:
            # Check if duckdb functions are available
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'duckdb_execute');"
            ))
            pg_duckdb_available = result.scalar()
            assert pg_duckdb_available is True, "duckdb_execute function not available"

    def test_timescaledb_functionality(self):
        """
        Test that timescaledb extension is functional.

        Verifies TimescaleDB hypertable functions are available.
        """
        with engine.connect() as conn:
            # Check if timescaledb functions are available
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'create_hypertable');"
            ))
            timescaledb_available = result.scalar()
            assert timescaledb_available is True, "create_hypertable function not available"

    def test_pg_cron_functionality(self):
        """
        Test that pg_cron extension is functional.

        Verifies cron job scheduling functions are available.
        """
        with engine.connect() as conn:
            # Check if pg_cron schema exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'cron');"
            ))
            pg_cron_available = result.scalar()
            assert pg_cron_available is True, "cron schema not available for pg_cron"

    def test_extensions_query_from_pg_extension(self):
        """
        Test that extensions can be queried from pg_extension table.

        Verifies PostgreSQL's internal tracking of installed extensions.
        """
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT extname FROM pg_extension WHERE extname = ANY(:ext_list);"
            ), {"ext_list": list(REQUIRED_EXTENSIONS)})

            installed_extensions = {row[0] for row in result}

            for ext_name in REQUIRED_EXTENSIONS:
                assert ext_name in installed_extensions, (
                    f"Extension {ext_name} not found in pg_extension table"
                )
