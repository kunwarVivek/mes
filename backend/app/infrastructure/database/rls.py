"""
Row-Level Security (RLS) context management

Provides functions to set and manage RLS context in PostgreSQL sessions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

def _get_settings() -> "Settings":
    """Lazy import settings to avoid circular dependency"""
    from app.core.config import settings
    return settings


def set_rls_context(db: Session, organization_id: int, plant_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    """
    Set RLS context variables in PostgreSQL session

    Args:
        db: SQLAlchemy database session
        organization_id: Organization ID for tenant isolation (required)
        plant_id: Plant ID for plant-level isolation (optional)
        user_id: Current authenticated user ID (optional, for audit trails)

    Side Effects:
        Sets PostgreSQL session variables:
        - app.current_organization_id
        - app.current_plant_id (if provided)
        - app.current_user_id (if provided)
    """
    if not _get_settings().RLS_ENABLED:
        return

    # Set organization_id in session (primary tenant isolation)
    db.execute(text("SET LOCAL app.current_organization_id = :org_id"), {"org_id": organization_id})

    # Set plant_id if provided (sub-tenant isolation)
    if plant_id is not None:
        db.execute(text("SET LOCAL app.current_plant_id = :plant_id"), {"plant_id": plant_id})

    # Set user_id if provided (for audit trails)
    if user_id is not None:
        db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": user_id})


def clear_rls_context(db: Session) -> None:
    """
    Clear RLS context variables from PostgreSQL session

    Args:
        db: SQLAlchemy database session
    """
    if not _get_settings().RLS_ENABLED:
        return

    db.execute(text("RESET app.current_organization_id"))
    db.execute(text("RESET app.current_plant_id"))
    db.execute(text("RESET app.current_user_id"))


def get_rls_context(db: Session) -> dict:
    """
    Get current RLS context from PostgreSQL session

    Args:
        db: SQLAlchemy database session

    Returns:
        Dictionary with organization_id, plant_id, and user_id
    """
    if not _get_settings().RLS_ENABLED:
        return {"organization_id": None, "plant_id": None, "user_id": None}

    result = db.execute(text("""
        SELECT
            current_setting('app.current_organization_id', true) as organization_id,
            current_setting('app.current_plant_id', true) as plant_id,
            current_setting('app.current_user_id', true) as user_id
    """))

    row = result.fetchone()

    return {
        "organization_id": int(row[0]) if row[0] else None,
        "plant_id": int(row[1]) if row[1] else None,
        "user_id": int(row[2]) if row[2] else None,
    }


def get_current_org_id(db: Session) -> Optional[int]:
    """
    Get current organization_id from RLS context

    Args:
        db: SQLAlchemy database session

    Returns:
        Current organization_id or None
    """
    if not _get_settings().RLS_ENABLED:
        return None

    try:
        result = db.execute(text("SELECT current_setting('app.current_organization_id', true)"))
        value = result.scalar()
        return int(value) if value else None
    except Exception:
        return None


def get_current_plant_id(db: Session) -> Optional[int]:
    """
    Get current plant_id from RLS context

    Args:
        db: SQLAlchemy database session

    Returns:
        Current plant_id or None
    """
    if not _get_settings().RLS_ENABLED:
        return None

    try:
        result = db.execute(text("SELECT current_setting('app.current_plant_id', true)"))
        value = result.scalar()
        return int(value) if value else None
    except Exception:
        return None
