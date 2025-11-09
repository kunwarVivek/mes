"""
PostgreSQL Extensions Management Module.

Provides utilities for verifying and managing PostgreSQL extensions:
- pgmq: Message queue for async job processing (30K msgs/sec throughput)
- pg_search: BM25 full-text search capabilities
- pg_duckdb: Analytics and OLAP query acceleration (10-100x faster)
- timescaledb: Time-series data compression and optimization
- pg_cron: Job scheduler for periodic tasks

Usage:
    from app.core.extensions import verify_extensions_installed
    from app.core.database import engine

    with engine.connect() as conn:
        if not verify_extensions_installed(conn):
            missing = get_missing_extensions(conn)
            print(f"Missing extensions: {missing}")
"""
from typing import Dict, Set, List, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
import logging


logger = logging.getLogger(__name__)


# Required PostgreSQL extensions for Unison
REQUIRED_EXTENSIONS: Set[str] = {
    "pgmq",
    "pg_search",
    "pg_duckdb",
    "timescaledb",
    "pg_cron"
}

# Extension descriptions for documentation
EXTENSION_DESCRIPTIONS: Dict[str, str] = {
    "pgmq": "Message queue for async job processing (30K msgs/sec)",
    "pg_search": "BM25 full-text search (replaces Elasticsearch)",
    "pg_duckdb": "Analytics and OLAP acceleration (10-100x faster)",
    "timescaledb": "Time-series compression (75% storage reduction)",
    "pg_cron": "Job scheduler for periodic tasks (replaces Celery Beat)"
}


def verify_extensions_installed(conn: Connection) -> bool:
    """
    Verify that all required PostgreSQL extensions are installed.

    Args:
        conn: SQLAlchemy database connection

    Returns:
        bool: True if all required extensions are installed, False otherwise
    """
    result = conn.execute(text(
        "SELECT extname FROM pg_extension WHERE extname = ANY(:ext_list);"
    ), {"ext_list": list(REQUIRED_EXTENSIONS)})

    installed_extensions = {row[0] for row in result}

    return REQUIRED_EXTENSIONS.issubset(installed_extensions)


def get_extension_versions(conn: Connection) -> Dict[str, str]:
    """
    Retrieve version information for all installed required extensions.

    Args:
        conn: SQLAlchemy database connection

    Returns:
        Dict[str, str]: Mapping of extension name to version string
    """
    result = conn.execute(text(
        """
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname = ANY(:ext_list);
        """
    ), {"ext_list": list(REQUIRED_EXTENSIONS)})

    return {row[0]: row[1] for row in result}


def get_missing_extensions(conn: Connection) -> Set[str]:
    """
    Identify which required extensions are not installed.

    Args:
        conn: SQLAlchemy database connection

    Returns:
        Set[str]: Set of extension names that are required but not installed
    """
    result = conn.execute(text(
        "SELECT extname FROM pg_extension WHERE extname = ANY(:ext_list);"
    ), {"ext_list": list(REQUIRED_EXTENSIONS)})

    installed_extensions = {row[0] for row in result}

    return REQUIRED_EXTENSIONS - installed_extensions


def check_extension_available(conn: Connection, extension_name: str) -> bool:
    """
    Check if an extension is available for installation (not necessarily installed).

    Args:
        conn: SQLAlchemy database connection
        extension_name: Name of the extension to check

    Returns:
        bool: True if extension is available in pg_available_extensions
    """
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = :ext_name);"
    ), {"ext_name": extension_name})

    return result.scalar()


def get_all_available_extensions(conn: Connection) -> List[Tuple[str, str, str]]:
    """
    Get list of all available PostgreSQL extensions in the database.

    Args:
        conn: SQLAlchemy database connection

    Returns:
        List[Tuple[str, str, str]]: List of (name, version, comment) tuples
    """
    try:
        result = conn.execute(text(
            """
            SELECT name, default_version, comment
            FROM pg_available_extensions
            ORDER BY name;
            """
        ))
        return [(row[0], row[1], row[2]) for row in result]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching available extensions: {e}")
        return []


def get_extension_info(conn: Connection, extension_name: str) -> Dict[str, str]:
    """
    Get detailed information about a specific extension.

    Args:
        conn: SQLAlchemy database connection
        extension_name: Name of the extension

    Returns:
        Dict[str, str]: Extension information including version, schema, etc.
        Returns empty dict if extension not found.
    """
    try:
        result = conn.execute(text(
            """
            SELECT
                e.extname,
                e.extversion,
                n.nspname as schema,
                e.extrelocatable,
                c.description
            FROM pg_extension e
            LEFT JOIN pg_namespace n ON n.oid = e.extnamespace
            LEFT JOIN pg_description c ON c.objoid = e.oid
            WHERE e.extname = :ext_name;
            """
        ), {"ext_name": extension_name})

        row = result.fetchone()
        if not row:
            return {}

        return {
            "name": row[0],
            "version": row[1],
            "schema": row[2],
            "relocatable": row[3],
            "description": row[4] or EXTENSION_DESCRIPTIONS.get(extension_name, "")
        }
    except SQLAlchemyError as e:
        logger.error(f"Error fetching extension info for {extension_name}: {e}")
        return {}


def verify_extensions_with_report(conn: Connection) -> Dict[str, any]:
    """
    Verify extensions and return detailed report.

    Args:
        conn: SQLAlchemy database connection

    Returns:
        Dict containing:
        - all_installed: bool
        - installed: List[str]
        - missing: List[str]
        - versions: Dict[str, str]
    """
    try:
        installed_extensions = {row[0] for row in conn.execute(text(
            "SELECT extname FROM pg_extension WHERE extname = ANY(:ext_list);"
        ), {"ext_list": list(REQUIRED_EXTENSIONS)})}

        missing_extensions = REQUIRED_EXTENSIONS - installed_extensions

        versions = {}
        if installed_extensions:
            result = conn.execute(text(
                """
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = ANY(:ext_list);
                """
            ), {"ext_list": list(installed_extensions)})
            versions = {row[0]: row[1] for row in result}

        return {
            "all_installed": len(missing_extensions) == 0,
            "installed": list(installed_extensions),
            "missing": list(missing_extensions),
            "versions": versions,
            "total_required": len(REQUIRED_EXTENSIONS)
        }
    except SQLAlchemyError as e:
        logger.error(f"Error verifying extensions: {e}")
        return {
            "all_installed": False,
            "installed": [],
            "missing": list(REQUIRED_EXTENSIONS),
            "versions": {},
            "total_required": len(REQUIRED_EXTENSIONS),
            "error": str(e)
        }
