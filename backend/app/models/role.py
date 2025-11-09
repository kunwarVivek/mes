"""
Role model for RBAC (Role-Based Access Control)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Role(Base):
    """
    Role definition for RBAC system.

    Supports:
    - Organization-scoped roles
    - System roles (pre-defined) vs custom roles
    - JSONB permissions for flexible access control
    - Integration with Casbin for enforcement
    """
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Role identification
    role_name = Column(String(100), nullable=False)
    role_code = Column(String(50), nullable=False)  # Unique identifier per org
    description = Column(Text, nullable=True)

    # System vs custom roles
    is_system_role = Column(Boolean, nullable=False, default=False)
    # System roles cannot be deleted, only deactivated

    # JSONB permissions structure:
    # {
    #   "materials": ["create", "read", "update", "delete"],
    #   "work_orders": ["*"],  # wildcard for all permissions
    #   "production": ["read", "update"]
    # }
    permissions = Column(JSONB, nullable=False, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'role_code', name='uq_role_code_per_org'),
        Index('idx_role_org', 'organization_id'),
        Index('idx_role_code', 'organization_id', 'role_code'),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, code='{self.role_code}', name='{self.role_name}')>"

    def has_permission(self, resource: str, action: str) -> bool:
        """
        Check if this role has a specific permission.

        Args:
            resource: Resource type (e.g., 'materials', 'work_orders')
            action: Action (e.g., 'create', 'read', 'update', 'delete')

        Returns:
            True if permission exists, False otherwise
        """
        if not self.permissions:
            return False

        # Check for wildcard permissions
        if "*" in self.permissions:
            if "*" in self.permissions["*"]:
                return True
            if action in self.permissions["*"]:
                return True

        # Check specific resource permissions
        if resource in self.permissions:
            resource_perms = self.permissions[resource]
            if "*" in resource_perms or action in resource_perms:
                return True

        return False


class UserRole(Base):
    """
    User-Role assignment with optional scope (plant/department level).

    Supports:
    - Organization-wide roles
    - Plant-scoped roles
    - Department-scoped roles
    - Role expiration
    - Audit trail (who assigned, when)
    """
    __tablename__ = 'user_roles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role_id = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=False, index=True)

    # Optional scope
    plant_id = Column(Integer, nullable=True)  # Null = org-wide
    department_id = Column(Integer, nullable=True)  # Null = all departments

    # Audit fields
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by = Column(Integer, nullable=True)  # User ID who assigned

    # Optional expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Active flag for soft delete
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    role = relationship("Role", back_populates="user_roles")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'plant_id', 'department_id',
                        name='uq_user_role_scope'),
        Index('idx_user_roles_user', 'user_id'),
        Index('idx_user_roles_role', 'role_id'),
        Index('idx_user_roles_org', 'organization_id'),
        Index('idx_user_roles_active', 'user_id', 'is_active'),
    )

    def __repr__(self):
        scope = ""
        if self.plant_id:
            scope = f", plant_id={self.plant_id}"
        if self.department_id:
            scope += f", dept_id={self.department_id}"
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id}{scope})>"

    def is_expired(self) -> bool:
        """Check if this role assignment has expired."""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at


class UserPlantAccess(Base):
    """
    Granular plant-level access control.

    Controls which plants a user can access and at what level.
    Separate from roles - this is infrastructure-level access.
    """
    __tablename__ = 'user_plant_access'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)

    # Access level (simplified)
    access_level = Column(String(50), nullable=False)  # READ, WRITE, ADMIN

    # Granular permissions
    can_create = Column(Boolean, nullable=False, default=False)
    can_read = Column(Boolean, nullable=False, default=True)
    can_update = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)

    # Audit fields
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    granted_by = Column(Integer, nullable=True)

    # Active flag
    is_active = Column(Boolean, nullable=False, default=True)

    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'plant_id', name='uq_user_plant_access'),
        Index('idx_user_plant_access_user', 'user_id'),
        Index('idx_user_plant_access_plant', 'plant_id'),
        Index('idx_user_plant_access_org', 'organization_id'),
    )

    def __repr__(self):
        return f"<UserPlantAccess(user_id={self.user_id}, plant_id={self.plant_id}, level='{self.access_level}')>"
