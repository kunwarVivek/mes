"""
RBAC Service - Business logic for Role-Based Access Control
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.role import Role, UserRole, UserPlantAccess
from app.infrastructure.repositories.role_repository import (
    RoleRepository,
    UserRoleRepository,
    UserPlantAccessRepository,
)
from app.application.dtos.role_dto import (
    RoleCreateDTO,
    RoleUpdateDTO,
    UserRoleAssignDTO,
    UserPlantAccessGrantDTO,
    PermissionCheckRequest,
)


class RBACService:
    """Service for Role-Based Access Control operations"""

    def __init__(self, db: Session):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.user_role_repo = UserRoleRepository(db)
        self.plant_access_repo = UserPlantAccessRepository(db)

    # ========== Role Management ==========

    def create_role(self, dto: RoleCreateDTO) -> Role:
        """Create a new custom role"""
        # Check if role code already exists
        existing = self.role_repo.get_by_code(dto.organization_id, dto.role_code)
        if existing:
            raise ValueError(f"Role with code '{dto.role_code}' already exists")

        return self.role_repo.create(dto)

    def get_role(self, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        return self.role_repo.get_by_id(role_id)

    def list_roles(self, organization_id: int, skip: int = 0, limit: int = 100,
                  include_system_roles: bool = True) -> List[Role]:
        """List all roles for an organization"""
        return self.role_repo.list(organization_id, skip, limit, include_system_roles)

    def update_role(self, role_id: int, dto: RoleUpdateDTO) -> Optional[Role]:
        """Update a custom role (cannot update system roles)"""
        return self.role_repo.update(role_id, dto)

    def delete_role(self, role_id: int) -> bool:
        """Delete a custom role (cannot delete system roles)"""
        # Check if role is assigned to any users
        users_with_role = self.user_role_repo.get_users_with_role(
            role_id,
            organization_id=None  # Will be filtered by RLS
        )
        if users_with_role:
            raise ValueError(
                f"Cannot delete role: {len(users_with_role)} user(s) still have this role"
            )

        return self.role_repo.delete(role_id)

    # ========== User Role Assignment ==========

    def assign_role_to_user(self, dto: UserRoleAssignDTO,
                           assigned_by: Optional[int] = None) -> UserRole:
        """Assign a role to a user"""
        # Verify role exists
        role = self.role_repo.get_by_id(dto.role_id)
        if not role:
            raise ValueError(f"Role with ID {dto.role_id} not found")

        # Check if user already has this role in this scope
        has_role = self.user_role_repo.has_role_in_scope(
            dto.user_id,
            dto.role_id,
            dto.plant_id,
            dto.department_id
        )
        if has_role:
            raise ValueError(
                f"User already has role '{role.role_name}' in this scope"
            )

        return self.user_role_repo.assign_role(dto, assigned_by)

    def revoke_user_role(self, user_role_id: int) -> bool:
        """Revoke a role from a user"""
        return self.user_role_repo.revoke_role(user_role_id)

    def get_user_roles(self, user_id: int, organization_id: int) -> List[UserRole]:
        """Get all active roles for a user"""
        return self.user_role_repo.get_user_roles(user_id, organization_id)

    def get_users_with_role(self, role_id: int, organization_id: int) -> List[UserRole]:
        """Get all users with a specific role"""
        return self.user_role_repo.get_users_with_role(role_id, organization_id)

    # ========== Plant Access Management ==========

    def grant_plant_access(self, dto: UserPlantAccessGrantDTO,
                          granted_by: Optional[int] = None) -> UserPlantAccess:
        """Grant plant access to a user"""
        # Check if access already exists
        existing = self.plant_access_repo.get_user_plant_access(dto.user_id, dto.plant_id)
        if existing:
            raise ValueError(
                f"User already has access to plant {dto.plant_id}. "
                "Use update endpoint to modify access level."
            )

        return self.plant_access_repo.grant_access(dto, granted_by)

    def revoke_plant_access(self, user_plant_access_id: int) -> bool:
        """Revoke plant access"""
        return self.plant_access_repo.revoke_access(user_plant_access_id)

    def get_user_accessible_plants(self, user_id: int, organization_id: int) -> List[UserPlantAccess]:
        """Get all plants accessible to a user"""
        return self.plant_access_repo.get_user_accessible_plants(user_id, organization_id)

    # ========== Permission Checking ==========

    def check_permission(self, request: PermissionCheckRequest) -> tuple[bool, Optional[str]]:
        """
        Check if user has permission for a specific resource/action.

        Returns: (has_permission, reason)
        """
        # Get user's roles in the relevant scope
        user_roles = self.user_role_repo.get_user_roles(
            request.user_id,
            organization_id=None  # Will be filtered by RLS
        )

        # Filter roles by scope (plant/department)
        relevant_roles = []
        for user_role in user_roles:
            # Skip expired roles
            if user_role.is_expired():
                continue

            # Check scope match
            if request.plant_id and user_role.plant_id:
                if user_role.plant_id != request.plant_id:
                    continue  # Role is scoped to different plant

            if request.department_id and user_role.department_id:
                if user_role.department_id != request.department_id:
                    continue  # Role is scoped to different department

            relevant_roles.append(user_role)

        if not relevant_roles:
            return False, "User has no active roles in this scope"

        # Check if any role grants the permission
        for user_role in relevant_roles:
            if user_role.role.has_permission(request.resource, request.action):
                return True, None

        return False, f"No role grants '{request.action}' permission on '{request.resource}'"

    def check_plant_access(self, user_id: int, plant_id: int,
                          required_action: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Check if user has access to a specific plant.

        Args:
            user_id: User ID
            plant_id: Plant ID
            required_action: Optional action (create, read, update, delete)

        Returns: (has_access, reason)
        """
        has_access = self.plant_access_repo.has_plant_access(
            user_id,
            plant_id,
            required_action
        )

        if not has_access:
            if required_action:
                return False, f"User does not have '{required_action}' access to plant {plant_id}"
            return False, f"User does not have access to plant {plant_id}"

        return True, None

    def get_user_permissions_summary(self, user_id: int, organization_id: int) -> dict:
        """
        Get a comprehensive summary of user's permissions.

        Returns dict with:
        - roles: List of assigned roles
        - plant_access: List of accessible plants
        - aggregated_permissions: Merged permissions from all roles
        """
        # Get user roles
        user_roles = self.user_role_repo.get_user_roles(user_id, organization_id)

        # Get plant access
        plant_access = self.plant_access_repo.get_user_accessible_plants(user_id, organization_id)

        # Aggregate permissions from all roles
        aggregated_permissions = {}
        for user_role in user_roles:
            if user_role.is_expired():
                continue

            role_perms = user_role.role.permissions or {}
            for resource, actions in role_perms.items():
                if resource not in aggregated_permissions:
                    aggregated_permissions[resource] = set()
                aggregated_permissions[resource].update(actions)

        # Convert sets to lists
        for resource in aggregated_permissions:
            aggregated_permissions[resource] = list(aggregated_permissions[resource])

        return {
            "roles": [
                {
                    "role_id": ur.role_id,
                    "role_name": ur.role.role_name,
                    "role_code": ur.role.role_code,
                    "plant_id": ur.plant_id,
                    "department_id": ur.department_id,
                    "expires_at": ur.expires_at,
                }
                for ur in user_roles if not ur.is_expired()
            ],
            "plant_access": [
                {
                    "plant_id": pa.plant_id,
                    "access_level": pa.access_level,
                    "can_create": pa.can_create,
                    "can_read": pa.can_read,
                    "can_update": pa.can_update,
                    "can_delete": pa.can_delete,
                }
                for pa in plant_access
            ],
            "aggregated_permissions": aggregated_permissions,
        }
