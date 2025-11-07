from fastapi import Depends, HTTPException, status
from app.domain.entities.user import User
from app.infrastructure.security.dependencies import get_current_user
from app.infrastructure.security.casbin_enforcer import casbin_enforcer


def require_permission(resource: str, action: str):
    """Dependency factory to check RBAC permissions"""

    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Determine user role
        role = "admin" if current_user.is_superuser else "user"

        # Check permission
        if not casbin_enforcer.enforce(role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No permission to {action} {resource}"
            )

        return current_user

    return permission_checker
