"""
DTOs for Role-Based Access Control (RBAC)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime


# ========== Role DTOs ==========

class RoleCreateDTO(BaseModel):
    """DTO for creating a new role"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    role_name: str = Field(..., min_length=1, max_length=100, description="Role display name")
    role_code: str = Field(..., min_length=1, max_length=50, description="Unique role code")
    description: Optional[str] = Field(None, description="Role description")
    permissions: Dict[str, List[str]] = Field(default_factory=dict, description="Permissions JSON")

    @field_validator('role_code')
    @classmethod
    def validate_role_code(cls, v):
        """Ensure role_code is uppercase and alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('role_code must be alphanumeric with underscores')
        return v.upper()

    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions structure"""
        if not isinstance(v, dict):
            raise ValueError('permissions must be a dictionary')

        # Validate each resource permissions
        valid_actions = ['create', 'read', 'update', 'delete', '*']
        for resource, actions in v.items():
            if not isinstance(actions, list):
                raise ValueError(f'permissions[{resource}] must be a list')
            for action in actions:
                if action not in valid_actions:
                    raise ValueError(f'Invalid action: {action}. Must be one of {valid_actions}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "role_name": "Production Manager",
                "role_code": "PRODUCTION_MANAGER",
                "description": "Manages production operations",
                "permissions": {
                    "work_orders": ["create", "read", "update", "delete"],
                    "production": ["*"],
                    "materials": ["read"]
                }
            }
        }


class RoleUpdateDTO(BaseModel):
    """DTO for updating an existing role"""
    role_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[Dict[str, List[str]]] = None

    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions structure"""
        if v is None:
            return v

        valid_actions = ['create', 'read', 'update', 'delete', '*']
        for resource, actions in v.items():
            if not isinstance(actions, list):
                raise ValueError(f'permissions[{resource}] must be a list')
            for action in actions:
                if action not in valid_actions:
                    raise ValueError(f'Invalid action: {action}')
        return v


class RoleResponse(BaseModel):
    """DTO for role response"""
    id: int
    organization_id: int
    role_name: str
    role_code: str
    description: Optional[str] = None
    is_system_role: bool
    permissions: Dict[str, List[str]]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "role_name": "Production Manager",
                "role_code": "PRODUCTION_MANAGER",
                "description": "Manages production operations",
                "is_system_role": False,
                "permissions": {
                    "work_orders": ["create", "read", "update", "delete"],
                    "production": ["*"]
                },
                "created_at": "2025-11-09T10:00:00Z",
                "updated_at": None
            }
        }


# ========== UserRole DTOs ==========

class UserRoleAssignDTO(BaseModel):
    """DTO for assigning a role to a user"""
    user_id: int = Field(..., gt=0)
    role_id: int = Field(..., gt=0)
    organization_id: int = Field(..., gt=0)
    plant_id: Optional[int] = Field(None, gt=0, description="Optional plant scope")
    department_id: Optional[int] = Field(None, gt=0, description="Optional department scope")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 5,
                "role_id": 3,
                "organization_id": 1,
                "plant_id": 2,
                "department_id": None,
                "expires_at": "2026-01-01T00:00:00Z"
            }
        }


class UserRoleResponse(BaseModel):
    """DTO for user role assignment response"""
    id: int
    user_id: int
    role_id: int
    organization_id: int
    plant_id: Optional[int] = None
    department_id: Optional[int] = None
    assigned_at: datetime
    assigned_by: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool

    # Nested role details
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True


class UserRoleRevokeDTO(BaseModel):
    """DTO for revoking a user role"""
    user_role_id: int = Field(..., gt=0, description="UserRole ID to revoke")


# ========== UserPlantAccess DTOs ==========

class UserPlantAccessGrantDTO(BaseModel):
    """DTO for granting plant access to a user"""
    user_id: int = Field(..., gt=0)
    plant_id: int = Field(..., gt=0)
    organization_id: int = Field(..., gt=0)
    access_level: str = Field(..., description="READ, WRITE, or ADMIN")
    can_create: bool = False
    can_read: bool = True
    can_update: bool = False
    can_delete: bool = False

    @field_validator('access_level')
    @classmethod
    def validate_access_level(cls, v):
        """Validate access level"""
        valid_levels = ['READ', 'WRITE', 'ADMIN']
        if v.upper() not in valid_levels:
            raise ValueError(f'access_level must be one of {valid_levels}')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 5,
                "plant_id": 2,
                "organization_id": 1,
                "access_level": "WRITE",
                "can_create": True,
                "can_read": True,
                "can_update": True,
                "can_delete": False
            }
        }


class UserPlantAccessResponse(BaseModel):
    """DTO for plant access response"""
    id: int
    user_id: int
    organization_id: int
    plant_id: int
    access_level: str
    can_create: bool
    can_read: bool
    can_update: bool
    can_delete: bool
    granted_at: datetime
    granted_by: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserPlantAccessRevokeDTO(BaseModel):
    """DTO for revoking plant access"""
    user_plant_access_id: int = Field(..., gt=0, description="UserPlantAccess ID to revoke")


# ========== Permission Check DTOs ==========

class PermissionCheckRequest(BaseModel):
    """DTO for checking if user has permission"""
    user_id: int = Field(..., gt=0)
    resource: str = Field(..., min_length=1, description="Resource type (e.g., 'materials')")
    action: str = Field(..., description="Action (e.g., 'create', 'read')")
    plant_id: Optional[int] = Field(None, gt=0, description="Optional plant context")
    department_id: Optional[int] = Field(None, gt=0, description="Optional department context")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action"""
        valid_actions = ['create', 'read', 'update', 'delete']
        if v not in valid_actions:
            raise ValueError(f'action must be one of {valid_actions}')
        return v


class PermissionCheckResponse(BaseModel):
    """DTO for permission check response"""
    has_permission: bool
    reason: Optional[str] = None  # Explanation if permission denied

    class Config:
        json_schema_extra = {
            "example": {
                "has_permission": True,
                "reason": None
            }
        }
