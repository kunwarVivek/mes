"""
Platform Admin Security Middleware

Provides authentication and authorization for platform admin endpoints.
All admin actions are logged for audit trail and security compliance.
"""
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Callable
import logging

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User
from app.infrastructure.logging.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


async def require_platform_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """
    Dependency to require platform admin (superuser) access.

    This dependency:
    1. Validates user is authenticated (via get_current_user)
    2. Checks if user has is_superuser=True
    3. Raises 403 Forbidden if not admin
    4. Logs all admin actions for audit trail

    Security Features:
    - Cross-organization access (bypasses RLS for admin operations)
    - All actions audited with admin_user_id, action, target, details
    - Rate limiting should be applied at route level for protection

    Args:
        current_user: Authenticated user from JWT token
        db: Database session for audit logging
        request: FastAPI request object for logging

    Returns:
        User: Authenticated platform admin user

    Raises:
        HTTPException 403: User is not a platform admin (is_superuser=False)

    Example:
        ```python
        @router.get("/admin/organizations")
        async def list_organizations(
            admin_user: User = Depends(require_platform_admin),
            db: Session = Depends(get_db)
        ):
            # Admin has full access across all organizations
            return get_all_organizations(db)
        ```
    """
    if not current_user.is_superuser:
        logger.warning(
            f"Unauthorized admin access attempt by user_id={current_user.id} "
            f"email={current_user.email.value}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Platform admin privileges required"
        )

    # Log successful admin authentication for audit trail
    logger.info(
        f"Platform admin access granted to user_id={current_user.id} "
        f"email={current_user.email.value}"
    )

    return current_user


def log_admin_action(
    admin_user: User,
    action: str,
    target_type: str,
    target_id: int = None,
    details: dict = None,
    db: Session = None
) -> None:
    """
    Log admin action for audit trail.

    All platform admin actions should be logged for:
    - Security auditing
    - Compliance requirements
    - Debugging and troubleshooting
    - Accountability

    Args:
        admin_user: Admin user performing action
        action: Action performed (e.g., "list_organizations", "suspend_subscription")
        target_type: Type of resource affected (e.g., "organization", "subscription")
        target_id: ID of affected resource (optional)
        details: Additional context (optional)
        db: Database session for persisting audit log

    Example:
        ```python
        log_admin_action(
            admin_user=admin_user,
            action="suspend_subscription",
            target_type="subscription",
            target_id=subscription_id,
            details={"reason": "Payment fraud detected"},
            db=db
        )
        ```
    """
    try:
        audit_logger = AuditLogger(db) if db else None

        log_data = {
            "admin_user_id": admin_user.id,
            "admin_email": admin_user.email.value,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details or {}
        }

        # Log to application logger
        logger.info(
            f"ADMIN ACTION: {action} by user_id={admin_user.id} "
            f"on {target_type}:{target_id or 'N/A'}"
        )

        # Persist to database audit log if db session provided
        if audit_logger:
            audit_logger.log_action(
                admin_user_id=admin_user.id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details
            )

    except Exception as e:
        # Never fail the operation due to audit logging errors
        # but log the error for investigation
        logger.error(f"Failed to log admin action: {e}", exc_info=True)


class AdminActionLogger:
    """
    Context manager for logging admin actions with automatic error handling.

    Usage:
        ```python
        async def suspend_organization(org_id: int, admin_user: User, db: Session):
            with AdminActionLogger(
                admin_user=admin_user,
                action="suspend_organization",
                target_type="organization",
                target_id=org_id,
                db=db
            ):
                # Perform admin operation
                organization.is_active = False
                db.commit()
        ```
    """

    def __init__(
        self,
        admin_user: User,
        action: str,
        target_type: str,
        target_id: int = None,
        details: dict = None,
        db: Session = None
    ):
        self.admin_user = admin_user
        self.action = action
        self.target_type = target_type
        self.target_id = target_id
        self.details = details or {}
        self.db = db

    def __enter__(self):
        """Log action start"""
        logger.debug(
            f"Starting admin action: {self.action} by user_id={self.admin_user.id}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log action completion or failure"""
        if exc_type is None:
            # Success - log the action
            self.details["status"] = "success"
            log_admin_action(
                admin_user=self.admin_user,
                action=self.action,
                target_type=self.target_type,
                target_id=self.target_id,
                details=self.details,
                db=self.db
            )
        else:
            # Failure - log with error details
            self.details["status"] = "failed"
            self.details["error"] = str(exc_val)
            log_admin_action(
                admin_user=self.admin_user,
                action=f"{self.action}_failed",
                target_type=self.target_type,
                target_id=self.target_id,
                details=self.details,
                db=self.db
            )

        # Don't suppress the exception
        return False
