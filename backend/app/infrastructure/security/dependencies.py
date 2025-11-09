from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict
from app.core.database import get_db
from app.infrastructure.persistence.user_repository_impl import UserRepository
from app.infrastructure.security.jwt_handler import JWTHandler
from app.domain.entities.user import User


security = HTTPBearer()
jwt_handler = JWTHandler()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user and set RLS context.

    This dependency:
    1. Validates JWT access token
    2. Extracts tenant context (organization_id, plant_id)
    3. Sets PostgreSQL session variables for RLS enforcement
    4. Returns authenticated user entity

    RLS Session Variables Set:
    - app.current_organization_id (REQUIRED - enforces tenant isolation)
    - app.current_plant_id (OPTIONAL - for plant-specific data access)

    Raises:
        HTTPException 401: Invalid/expired token, user not found, inactive user
        HTTPException 403: Missing organization_id (RLS requires tenant context)
    """
    token = credentials.credentials

    try:
        payload = jwt_handler.decode_token(token)

        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Extract tenant context from JWT
        organization_id = payload.get("organization_id")
        plant_id = payload.get("plant_id")

        # Validate tenant context - organization_id is REQUIRED for RLS
        if organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token missing organization_id - tenant context required for RLS enforcement"
            )

        user_id = int(payload.get("sub"))

        # Get user from database
        repository = UserRepository(db)
        user = repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )

        # Set PostgreSQL RLS session variables for tenant isolation
        # These are used by RLS policies (53 policies across 28 tables) to enforce
        # multi-tenant data isolation at the database level
        _set_rls_context(db, organization_id, plant_id)

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


def _set_rls_context(
    db: Session,
    organization_id: int,
    plant_id: int = None
) -> None:
    """
    Set PostgreSQL session variables for Row-Level Security (RLS) enforcement.

    Session variables are set using SET LOCAL to ensure they only persist for the
    current transaction and are automatically cleared after commit/rollback.

    Args:
        db: SQLAlchemy session
        organization_id: Required organization ID for tenant isolation
        plant_id: Optional plant ID for plant-specific data access
    """
    # Always set organization_id (required for RLS)
    db.execute(text(f"SET LOCAL app.current_organization_id = {organization_id}"))

    # Only set plant_id if user has a plant assignment
    # Organization-level users (admins, managers) may not have plant assignments
    if plant_id is not None:
        db.execute(text(f"SET LOCAL app.current_plant_id = {plant_id}"))


def get_user_context(request: Request) -> Dict[str, any]:
    """
    Get user context from request state (set by auth_middleware).

    Returns dict with: id, email, organization_id, plant_id

    This is used by material endpoints that need org/plant context for RLS.
    """
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to require superuser access"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
