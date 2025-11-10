from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.domain.entities.user import User
from app.infrastructure.security.dependencies import get_current_user
from app.infrastructure.security.casbin_enforcer import casbin_enforcer
from app.core.database import get_db
from app.models.role import UserRole


def require_permission(resource: str, action: str):
    """
    Dependency factory to check RBAC permissions.

    Usage:
        @router.delete("/work-orders/{id}")
        async def delete_work_order(
            id: int,
            current_user: User = Depends(require_permission("work_orders", "delete"))
        ):
            ...

    Args:
        resource: Resource type (e.g., "work_orders", "materials", "ncrs")
        action: Action type (e.g., "view", "create", "update", "delete")

    Returns:
        Dependency function that validates permission and returns current_user

    Raises:
        HTTPException 403: If user lacks required permission
    """

    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user

        # Get user's roles from database
        user_roles = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.is_active == True
        ).all()

        # Check if user has no roles (should not happen in normal flow)
        if not user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User has no assigned roles"
            )

        # Check permission for each role
        has_permission = False
        for user_role in user_roles:
            role_name = user_role.role.role_name if user_role.role else "user"

            # Check Casbin policy
            if casbin_enforcer.enforce(role_name, resource, action):
                has_permission = True
                break

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to {action} {resource}"
            )

        return current_user

    return permission_checker
