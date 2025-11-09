"""
Unit tests for PostgreSQL extensions verification logic.

Tests the extension verification functions without requiring database connection.
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.core.extensions import (
    verify_extensions_installed,
    get_extension_versions,
    get_missing_extensions,
    check_extension_available,
    REQUIRED_EXTENSIONS
)


class TestExtensionsLogic:
    """Unit tests for extensions module logic."""

    def test_required_extensions_constant(self):
        """Test that REQUIRED_EXTENSIONS contains expected extensions."""
        expected = {"pgmq", "pg_search", "pg_duckdb", "timescaledb", "pg_cron"}
        assert REQUIRED_EXTENSIONS == expected

    def test_verify_extensions_installed_all_present(self):
        """Test verification when all extensions are installed."""
        # Mock connection
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            ("pgmq",),
            ("pg_search",),
            ("pg_duckdb",),
            ("timescaledb",),
            ("pg_cron",)
        ]))
        mock_conn.execute.return_value = mock_result

        result = verify_extensions_installed(mock_conn)
        assert result is True

    def test_verify_extensions_installed_missing_some(self):
        """Test verification when some extensions are missing."""
        # Mock connection with only 2 extensions
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            ("pgmq",),
            ("pg_search",)
        ]))
        mock_conn.execute.return_value = mock_result

        result = verify_extensions_installed(mock_conn)
        assert result is False

    def test_verify_extensions_installed_none_present(self):
        """Test verification when no extensions are installed."""
        # Mock connection with no extensions
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_conn.execute.return_value = mock_result

        result = verify_extensions_installed(mock_conn)
        assert result is False

    def test_get_extension_versions_all_present(self):
        """Test getting versions when all extensions are installed."""
        # Mock connection
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            ("pgmq", "1.0.0"),
            ("pg_search", "0.5.0"),
            ("pg_duckdb", "0.1.0"),
            ("timescaledb", "2.11.0"),
            ("pg_cron", "1.5.0")
        ]))
        mock_conn.execute.return_value = mock_result

        versions = get_extension_versions(mock_conn)

        assert len(versions) == 5
        assert versions["pgmq"] == "1.0.0"
        assert versions["pg_search"] == "0.5.0"
        assert versions["pg_duckdb"] == "0.1.0"
        assert versions["timescaledb"] == "2.11.0"
        assert versions["pg_cron"] == "1.5.0"

    def test_get_extension_versions_partial(self):
        """Test getting versions when only some extensions are installed."""
        # Mock connection with partial extensions
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            ("pgmq", "1.0.0"),
            ("timescaledb", "2.11.0")
        ]))
        mock_conn.execute.return_value = mock_result

        versions = get_extension_versions(mock_conn)

        assert len(versions) == 2
        assert "pgmq" in versions
        assert "timescaledb" in versions
        assert "pg_search" not in versions

    def test_get_missing_extensions_none_missing(self):
        """Test identifying missing extensions when all are installed."""
        # Mock connection with all extensions
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            ("pgmq",),
            ("pg_search",),
            ("pg_duckdb",),
            ("timescaledb",),
            ("pg_cron",)
        ]))
        mock_conn.execute.return_value = mock_result

        missing = get_missing_extensions(mock_conn)
        assert len(missing) == 0

    def test_get_missing_extensions_some_missing(self):
        """Test identifying missing extensions when some are not installed."""
        # Mock connection with only 2 extensions
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            ("pgmq",),
            ("pg_search",)
        ]))
        mock_conn.execute.return_value = mock_result

        missing = get_missing_extensions(mock_conn)

        assert len(missing) == 3
        assert "pg_duckdb" in missing
        assert "timescaledb" in missing
        assert "pg_cron" in missing

    def test_get_missing_extensions_all_missing(self):
        """Test identifying missing extensions when none are installed."""
        # Mock connection with no extensions
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_conn.execute.return_value = mock_result

        missing = get_missing_extensions(mock_conn)

        assert len(missing) == 5
        assert missing == REQUIRED_EXTENSIONS

    def test_check_extension_available_exists(self):
        """Test checking if extension is available when it exists."""
        # Mock connection
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = True
        mock_conn.execute.return_value = mock_result

        result = check_extension_available(mock_conn, "pgmq")
        assert result is True

    def test_check_extension_available_not_exists(self):
        """Test checking if extension is available when it doesn't exist."""
        # Mock connection
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = False
        mock_conn.execute.return_value = mock_result

        result = check_extension_available(mock_conn, "non_existent")
        assert result is False
