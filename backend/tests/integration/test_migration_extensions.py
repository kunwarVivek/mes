"""
Integration test for PostgreSQL extensions migration.

Tests the Alembic migration script that installs extensions.
Requires a PostgreSQL database with extensions available.
"""
import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.extensions import (
    verify_extensions_installed,
    get_extension_versions,
    get_missing_extensions,
    REQUIRED_EXTENSIONS
)


@pytest.fixture(scope="module")
def db_engine():
    """Create a database engine for testing."""
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db_connection(db_engine):
    """Create a database connection for testing."""
    connection = db_engine.connect()
    yield connection
    connection.close()


class TestExtensionsMigration:
    """Integration tests for extensions migration."""

    def test_database_connection(self, db_connection):
        """Test that database connection works."""
        result = db_connection.execute(text("SELECT 1;"))
        assert result.scalar() == 1

    def test_check_available_extensions(self, db_connection):
        """
        Check which required extensions are available for installation.

        This is informational - it shows what's available in the PostgreSQL instance.
        """
        result = db_connection.execute(text(
            """
            SELECT name, default_version, installed_version, comment
            FROM pg_available_extensions
            WHERE name = ANY(:ext_list)
            ORDER BY name;
            """
        ), {"ext_list": list(REQUIRED_EXTENSIONS)})

        available = {}
        for row in result:
            name, default_ver, installed_ver, comment = row
            available[name] = {
                "default_version": default_ver,
                "installed_version": installed_ver,
                "comment": comment
            }

        print("\nAvailable extensions in PostgreSQL instance:")
        for ext_name in REQUIRED_EXTENSIONS:
            if ext_name in available:
                info = available[ext_name]
                status = "INSTALLED" if info["installed_version"] else "AVAILABLE"
                print(f"  ✓ {ext_name}: {status} (v{info['default_version']})")
            else:
                print(f"  ✗ {ext_name}: NOT AVAILABLE")

    @pytest.mark.skipif(
        True,
        reason="Requires running migration: alembic upgrade head"
    )
    def test_extensions_installed_after_migration(self, db_connection):
        """
        Test that all extensions are installed after migration runs.

        To enable this test:
        1. Run: cd backend && alembic upgrade head
        2. Remove @pytest.mark.skipif decorator
        3. Run: pytest tests/integration/test_migration_extensions.py -v
        """
        result = verify_extensions_installed(db_connection)
        assert result is True, "Not all required extensions are installed"

    @pytest.mark.skipif(
        True,
        reason="Requires running migration: alembic upgrade head"
    )
    def test_extension_versions_retrievable(self, db_connection):
        """
        Test that extension versions can be retrieved after migration.

        To enable this test:
        1. Run: cd backend && alembic upgrade head
        2. Remove @pytest.mark.skipif decorator
        """
        versions = get_extension_versions(db_connection)

        for ext_name in REQUIRED_EXTENSIONS:
            assert ext_name in versions, f"Extension {ext_name} not in versions dict"
            assert versions[ext_name] is not None, f"Extension {ext_name} has no version"
            print(f"  {ext_name}: v{versions[ext_name]}")

    @pytest.mark.skipif(
        True,
        reason="Requires running migration: alembic upgrade head"
    )
    def test_no_missing_extensions_after_migration(self, db_connection):
        """
        Test that no extensions are missing after migration.

        To enable this test:
        1. Run: cd backend && alembic upgrade head
        2. Remove @pytest.mark.skipif decorator
        """
        missing = get_missing_extensions(db_connection)
        assert len(missing) == 0, f"Missing extensions: {missing}"

    def test_migration_script_exists(self):
        """Test that the migration script file exists."""
        import os
        migration_file = "/Users/vivek/jet/unison/database/migrations/versions/001_install_postgresql_extensions.py"
        assert os.path.exists(migration_file), "Migration script not found"

    def test_migration_has_upgrade_and_downgrade(self):
        """Test that migration script has both upgrade and downgrade functions."""
        import sys
        sys.path.insert(0, "/Users/vivek/jet/unison/database/migrations/versions")

        from importlib import import_module
        migration = import_module("001_install_postgresql_extensions")

        assert hasattr(migration, "upgrade"), "Migration missing upgrade function"
        assert hasattr(migration, "downgrade"), "Migration missing downgrade function"
        assert callable(migration.upgrade), "upgrade is not callable"
        assert callable(migration.downgrade), "downgrade is not callable"
