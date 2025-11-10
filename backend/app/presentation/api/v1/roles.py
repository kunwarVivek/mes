"""
API endpoints for Role-Based Access Control (RBAC)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.services.rbac_service import RBACService
from app.application.dtos.role_dto import (
    RoleCreateDTO,
    RoleUpdateDTO,
    RoleResponse,
    UserRoleAssignDTO,
    UserRoleResponse,
    UserRoleRevokeDTO,
    UserPlantAccessGrantDTO,
    UserPlantAccessResponse,
    UserPlantAccessRevokeDTO,
    PermissionCheckRequest,
    PermissionCheckResponse,
)

router = APIRouter(prefix="/roles", tags=["rbac"])


# ========== Role Management Endpoints ==========

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    dto: RoleCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new custom role.

    **Requires:** SUPER_ADMIN role or 'roles' create permission
    """
    service = RBACService(db)

    try:
        role = service.create_role(dto)
        return RoleResponse.from_orm(role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    include_system_roles: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all roles for current organization.

    **Query Params:**
    - skip: Pagination offset
    - limit: Max results
    - include_system_roles: Include predefined system roles
    """
    service = RBACService(db)
    organization_id = current_user.get("organization_id")

    roles = service.list_roles(organization_id, skip, limit, include_system_roles)
    return [RoleResponse.from_orm(role) for role in roles]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get role by ID"""
    service = RBACService(db)
    role = service.get_role(role_id)

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    return RoleResponse.from_orm(role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    dto: RoleUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a custom role.

    **Note:** System roles cannot be modified.
    """
    service = RBACService(db)

    try:
        role = service.update_role(role_id, dto)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        return RoleResponse.from_orm(role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a custom role.

    **Note:**
    - System roles cannot be deleted
    - Roles assigned to users cannot be deleted
    """
    service = RBACService(db)

    try:
        success = service.delete_role(role_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== User Role Assignment Endpoints ==========

@router.post("/assign", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    dto: UserRoleAssignDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a role to a user.

    **Optional Scope:**
    - plant_id: Scope role to specific plant
    - department_id: Scope role to specific department
    - expires_at: Set expiration date
    """
    service = RBACService(db)
    assigned_by = current_user.get("id")

    try:
        user_role = service.assign_role_to_user(dto, assigned_by)
        return UserRoleResponse.from_orm(user_role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_role(
    dto: UserRoleRevokeDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Revoke a role from a user"""
    service = RBACService(db)

    success = service.revoke_user_role(dto.user_role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse])
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all active roles for a user"""
    service = RBACService(db)
    organization_id = current_user.get("organization_id")

    user_roles = service.get_user_roles(user_id, organization_id)
    return [UserRoleResponse.from_orm(ur) for ur in user_roles]


@router.get("/{role_id}/users", response_model=List[UserRoleResponse])
async def get_role_users(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all users with a specific role"""
    service = RBACService(db)
    organization_id = current_user.get("organization_id")

    user_roles = service.get_users_with_role(role_id, organization_id)
    return [UserRoleResponse.from_orm(ur) for ur in user_roles]


# ========== Plant Access Endpoints ==========

@router.post("/plant-access/grant", response_model=UserPlantAccessResponse,
            status_code=status.HTTP_201_CREATED)
async def grant_plant_access(
    dto: UserPlantAccessGrantDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Grant plant-level access to a user"""
    service = RBACService(db)
    granted_by = current_user.get("id")

    try:
        access = service.grant_plant_access(dto, granted_by)
        return UserPlantAccessResponse.from_orm(access)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/plant-access/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_plant_access(
    dto: UserPlantAccessRevokeDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Revoke plant-level access"""
    service = RBACService(db)

    success = service.revoke_plant_access(dto.user_plant_access_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant access not found")


@router.get("/users/{user_id}/plant-access", response_model=List[UserPlantAccessResponse])
async def get_user_plant_access(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all plant access for a user"""
    service = RBACService(db)
    organization_id = current_user.get("organization_id")

    plant_access = service.get_user_accessible_plants(user_id, organization_id)
    return [UserPlantAccessResponse.from_orm(pa) for pa in plant_access]


# ========== Permission Checking Endpoints ==========

@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    request: PermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Check if a user has a specific permission.

    **Use Case:** Frontend authorization checks before showing UI elements
    """
    service = RBACService(db)

    has_permission, reason = service.check_permission(request)
    return PermissionCheckResponse(has_permission=has_permission, reason=reason)


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive permissions summary for a user.

    **Returns:**
    - All assigned roles (with scope)
    - All accessible plants
    - Aggregated permissions from all roles
    """
    service = RBACService(db)
    organization_id = current_user.get("organization_id")

    return service.get_user_permissions_summary(user_id, organization_id)
