"""Install PostgreSQL extensions for Unison ERP

Revision ID: 001_install_extensions
Revises:
Create Date: 2025-11-08 02:00:00.000000

Extensions installed:
- pgmq: Message queue for async job processing (30K msgs/sec throughput)
- pg_search: BM25 full-text search capabilities (replaces Elasticsearch)
- pg_duckdb: Analytics and OLAP query acceleration (10-100x faster)
- timescaledb: Time-series data compression and optimization (75% compression)
- pg_cron: Job scheduler for periodic tasks (replaces Celery Beat)

Note: These extensions must be available in the PostgreSQL installation.
For production: Use tembo/tembo-pg-slim or install extensions manually.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '001_install_extensions'
down_revision = None
branch_labels = None
depends_on = None


REQUIRED_EXTENSIONS = [
    ('pgmq', 'Message queue for async job processing'),
    ('pg_search', 'BM25 full-text search capabilities'),
    ('pg_duckdb', 'Analytics and OLAP query acceleration'),
    ('timescaledb', 'Time-series data compression'),
    ('pg_cron', 'Job scheduler for periodic tasks'),
]

STANDARD_EXTENSIONS = [
    ('uuid-ossp', 'UUID generation functions'),
    ('pg_trgm', 'Trigram similarity for fuzzy search'),
    ('btree_gin', 'GIN indexes for multi-column queries'),
]


def upgrade() -> None:
    """
    Install all required PostgreSQL extensions.

    This migration installs extensions in a specific order:
    1. Standard PostgreSQL extensions (uuid-ossp, pg_trgm, btree_gin)
    2. Core extensions (timescaledb, pgmq, pg_cron, pg_search, pg_duckdb)

    Note: Extensions must be available via CREATE EXTENSION.
    Verify with: SELECT * FROM pg_available_extensions;
    """
    conn = op.get_bind()

    # Install standard extensions first
    print("\nInstalling standard PostgreSQL extensions...")
    for ext_name, description in STANDARD_EXTENSIONS:
        try:
            print(f"  Installing {ext_name}: {description}")
            conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext_name}";'))
            conn.commit()
            print(f"    ✓ {ext_name} installed successfully")
        except Exception as e:
            print(f"    ✗ Failed to install {ext_name}: {e}")
            raise

    # Install required extensions
    print("\nInstalling required Unison extensions...")
    for ext_name, description in REQUIRED_EXTENSIONS:
        try:
            print(f"  Installing {ext_name}: {description}")
            conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS {ext_name};'))
            conn.commit()
            print(f"    ✓ {ext_name} installed successfully")
        except Exception as e:
            print(f"    ✗ Failed to install {ext_name}: {e}")
            print(f"    Note: Ensure {ext_name} is available in pg_available_extensions")
            raise

    # Verify all extensions are installed
    print("\nVerifying installed extensions...")
    all_extensions = [ext[0] for ext in STANDARD_EXTENSIONS + REQUIRED_EXTENSIONS]
    result = conn.execute(text(
        """
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname = ANY(:ext_list)
        ORDER BY extname;
        """
    ), {"ext_list": all_extensions})

    installed = []
    for row in result:
        ext_name, ext_version = row
        installed.append(ext_name)
        print(f"  ✓ {ext_name} version {ext_version}")

    # Check for missing extensions
    missing = set(all_extensions) - set(installed)
    if missing:
        raise Exception(f"Missing extensions after installation: {missing}")

    print("\n✅ All PostgreSQL extensions installed successfully!")


def downgrade() -> None:
    """
    Uninstall all PostgreSQL extensions.

    WARNING: This will drop all extensions and their dependent objects.
    Use with caution in production environments.

    Extensions are dropped in reverse order to handle dependencies.
    """
    conn = op.get_bind()

    print("\n⚠️  Uninstalling PostgreSQL extensions...")

    # Drop required extensions in reverse order
    for ext_name, description in reversed(REQUIRED_EXTENSIONS):
        try:
            print(f"  Dropping {ext_name}...")
            conn.execute(text(f'DROP EXTENSION IF EXISTS {ext_name} CASCADE;'))
            conn.commit()
            print(f"    ✓ {ext_name} dropped")
        except Exception as e:
            print(f"    ✗ Failed to drop {ext_name}: {e}")
            # Continue with other extensions even if one fails

    # Drop standard extensions in reverse order
    for ext_name, description in reversed(STANDARD_EXTENSIONS):
        try:
            print(f"  Dropping {ext_name}...")
            conn.execute(text(f'DROP EXTENSION IF EXISTS "{ext_name}" CASCADE;'))
            conn.commit()
            print(f"    ✓ {ext_name} dropped")
        except Exception as e:
            print(f"    ✗ Failed to drop {ext_name}: {e}")
            # Continue with other extensions even if one fails

    print("\n✅ PostgreSQL extensions uninstalled")
