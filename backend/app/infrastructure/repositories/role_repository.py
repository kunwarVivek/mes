"""
Repository for Role-Based Access Control (RBAC)
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime, timezone

from app.models.role import Role, UserRole, UserPlantAccess
from app.application.dtos.role_dto import (
    RoleCreateDTO,
    RoleUpdateDTO,
    UserRoleAssignDTO,
    UserPlantAccessGrantDTO,
)


class RoleRepository:
    """Repository for Role operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: RoleCreateDTO) -> Role:
        """Create a new role"""
        role = Role(
            organization_id=dto.organization_id,
            role_name=dto.role_name,
            role_code=dto.role_code,
            description=dto.description,
            is_system_role=False,  # User-created roles are never system roles
            permissions=dto.permissions or {},
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_by_code(self, organization_id: int, role_code: str) -> Optional[Role]:
        """Get role by code within an organization"""
        return self.db.query(Role).filter(
            and_(
                Role.organization_id == organization_id,
                Role.role_code == role_code
            )
        ).first()

    def list(self, organization_id: int, skip: int = 0, limit: int = 100,
            include_system_roles: bool = True) -> List[Role]:
        """List roles for an organization"""
        query = self.db.query(Role).filter(Role.organization_id == organization_id)

        if not include_system_roles:
            query = query.filter(Role.is_system_role == False)

        return query.offset(skip).limit(limit).all()

    def update(self, role_id: int, dto: RoleUpdateDTO) -> Optional[Role]:
        """Update role (only for non-system roles)"""
        role = self.get_by_id(role_id)
        if not role:
            return None

        # Prevent updates to system roles
        if role.is_system_role:
            raise ValueError("Cannot modify system roles")

        if dto.role_name:
            role.role_name = dto.role_name
        if dto.description is not None:
            role.description = dto.description
        if dto.permissions is not None:
            role.permissions = dto.permissions

        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role_id: int) -> bool:
        """Delete role (only for non-system roles)"""
        role = self.get_by_id(role_id)
        if not role:
            return False

        # Prevent deletion of system roles
        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        self.db.delete(role)
        self.db.commit()
        return True

    def get_system_roles(self, organization_id: int) -> List[Role]:
        """Get all system roles for an organization"""
        return self.db.query(Role).filter(
            and_(
                Role.organization_id == organization_id,
                Role.is_system_role == True
            )
        ).all()


class UserRoleRepository:
    """Repository for UserRole operations"""

    def __init__(self, db: Session):
        self.db = db

    def assign_role(self, dto: UserRoleAssignDTO, assigned_by: Optional[int] = None) -> UserRole:
        """Assign a role to a user"""
        user_role = UserRole(
            user_id=dto.user_id,
            role_id=dto.role_id,
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            department_id=dto.department_id,
            assigned_by=assigned_by,
            expires_at=dto.expires_at,
            is_active=True,
        )
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role

    def revoke_role(self, user_role_id: int) -> bool:
        """Revoke a role assignment (soft delete)"""
        user_role = self.db.query(UserRole).filter(UserRole.id == user_role_id).first()
        if not user_role:
            return False

        user_role.is_active = False
        self.db.commit()
        return True

    def get_user_roles(self, user_id: int, organization_id: int,
                      include_inactive: bool = False) -> List[UserRole]:
        """Get all roles assigned to a user"""
        query = self.db.query(UserRole).options(joinedload(UserRole.role)).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.organization_id == organization_id
            )
        )

        if not include_inactive:
            query = query.filter(UserRole.is_active == True)

        return query.all()

    def get_users_with_role(self, role_id: int, organization_id: int) -> List[UserRole]:
        """Get all users with a specific role"""
        return self.db.query(UserRole).options(joinedload(UserRole.role)).filter(
            and_(
                UserRole.role_id == role_id,
                UserRole.organization_id == organization_id,
                UserRole.is_active == True
            )
        ).all()

    def has_role_in_scope(self, user_id: int, role_id: int,
                         plant_id: Optional[int] = None,
                         department_id: Optional[int] = None) -> bool:
        """Check if user has a specific role in given scope"""
        query = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            )
        )

        # Check for exact scope or org-wide (null scope)
        if plant_id:
            query = query.filter(
                or_(
                    UserRole.plant_id == plant_id,
                    UserRole.plant_id == None  # Org-wide role
                )
            )

        if department_id:
            query = query.filter(
                or_(
                    UserRole.department_id == department_id,
                    UserRole.department_id == None
                )
            )

        return query.first() is not None


class UserPlantAccessRepository:
    """Repository for UserPlantAccess operations"""

    def __init__(self, db: Session):
        self.db = db

    def grant_access(self, dto: UserPlantAccessGrantDTO,
                    granted_by: Optional[int] = None) -> UserPlantAccess:
        """Grant plant access to a user"""
        access = UserPlantAccess(
            user_id=dto.user_id,
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            access_level=dto.access_level,
            can_create=dto.can_create,
            can_read=dto.can_read,
            can_update=dto.can_update,
            can_delete=dto.can_delete,
            granted_by=granted_by,
            is_active=True,
        )
        self.db.add(access)
        self.db.commit()
        self.db.refresh(access)
        return access

    def revoke_access(self, user_plant_access_id: int) -> bool:
        """Revoke plant access (soft delete)"""
        access = self.db.query(UserPlantAccess).filter(
            UserPlantAccess.id == user_plant_access_id
        ).first()
        if not access:
            return False

        access.is_active = False
        self.db.commit()
        return True

    def get_user_plant_access(self, user_id: int, plant_id: int) -> Optional[UserPlantAccess]:
        """Get user's access to a specific plant"""
        return self.db.query(UserPlantAccess).filter(
            and_(
                UserPlantAccess.user_id == user_id,
                UserPlantAccess.plant_id == plant_id,
                UserPlantAccess.is_active == True
            )
        ).first()

    def get_user_accessible_plants(self, user_id: int, organization_id: int) -> List[UserPlantAccess]:
        """Get all plants accessible to a user"""
        return self.db.query(UserPlantAccess).filter(
            and_(
                UserPlantAccess.user_id == user_id,
                UserPlantAccess.organization_id == organization_id,
                UserPlantAccess.is_active == True
            )
        ).all()

    def has_plant_access(self, user_id: int, plant_id: int, required_action: Optional[str] = None) -> bool:
        """Check if user has access to a plant with optional action check"""
        access = self.get_user_plant_access(user_id, plant_id)
        if not access:
            return False

        if required_action:
            action_map = {
                'create': access.can_create,
                'read': access.can_read,
                'update': access.can_update,
                'delete': access.can_delete,
            }
            return action_map.get(required_action, False)

        return True
